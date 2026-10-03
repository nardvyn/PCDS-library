from datetime import datetime, timezone, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.book import Book
from app.models.borrow_request import BorrowRequest
from app.models.loan import Loan
from app.models.notification import Notification
from app.models.penalty import Penalty
from app.models.library_setting import LibrarySetting
from app.models.user import User
from app.services.audit_service import record_audit

library_bp = Blueprint("library_operations", __name__, url_prefix="/api/library")


def staff_access_required():
    return get_jwt().get("role") in {"ADMIN", "LIBRARIAN"}


def denied_response():
    return jsonify({"success": False, "message": "Librarian or administrator access is required."}), 403


DEFAULT_SETTINGS = {
    "student_loan_days": "7",
    "teacher_loan_days": "14",
    "daily_penalty": "10.00",
    "notifications_enabled": "true",
}


def get_library_settings():
    rows = {row.setting_key: row.setting_value for row in LibrarySetting.query.all()}
    return {key: rows.get(key, default) for key, default in DEFAULT_SETTINGS.items()}


@library_bp.get("/settings")
@jwt_required()
def read_library_settings():
    if get_jwt().get("role") != "ADMIN":
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    settings = get_library_settings()
    return jsonify({
        "success": True,
        "settings": {
            "student_loan_days": int(settings["student_loan_days"]),
            "teacher_loan_days": int(settings["teacher_loan_days"]),
            "daily_penalty": float(settings["daily_penalty"]),
            "notifications_enabled": settings["notifications_enabled"].lower() == "true",
        },
    }), 200


@library_bp.put("/settings")
@jwt_required()
def save_library_settings():
    if get_jwt().get("role") != "ADMIN":
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    data = request.get_json(silent=True) or {}
    try:
        student_days = int(data.get("student_loan_days", 7))
        teacher_days = int(data.get("teacher_loan_days", 14))
        daily_penalty = Decimal(str(data.get("daily_penalty", 10)))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Loan periods and penalty must be valid numbers."}), 400
    if not 1 <= student_days <= 365 or not 1 <= teacher_days <= 365 or not Decimal("0") <= daily_penalty <= Decimal("100000"):
        return jsonify({"success": False, "message": "Loan periods must be 1-365 days and penalty must be between 0 and 100000."}), 400

    values = {
        "student_loan_days": str(student_days),
        "teacher_loan_days": str(teacher_days),
        "daily_penalty": f"{daily_penalty:.2f}",
        "notifications_enabled": "true" if data.get("notifications_enabled", True) else "false",
    }
    current_settings = get_library_settings()
    adjusted_loan_count = 0
    changed_periods = (
        ("STUDENT", "student_loan_days", student_days),
        ("TEACHER", "teacher_loan_days", teacher_days),
    )
    for role, setting_key, loan_days in changed_periods:
        if int(current_settings[setting_key]) == loan_days:
            continue
        active_loans = (
            Loan.query.join(User, Loan.user_id == User.user_id)
            .filter(Loan.status == "ACTIVE", User.role == role)
            .all()
        )
        for loan in active_loans:
            loan.due_date = loan.borrowed_at + timedelta(days=loan_days)
        adjusted_loan_count += len(active_loans)

    actor_id = int(get_jwt_identity())
    for key, value in values.items():
        setting = db.session.get(LibrarySetting, key)
        if setting is None:
            setting = LibrarySetting(setting_key=key, setting_value=value, updated_by=actor_id)
            db.session.add(setting)
        else:
            setting.setting_value = value
            setting.updated_by = actor_id
    record_audit(actor_id, "LIBRARY_SETTINGS_UPDATED", "SETTINGS", None, f"Student loan {student_days} days; teacher loan {teacher_days} days; daily penalty PHP {daily_penalty:.2f}; active loan due dates adjusted: {adjusted_loan_count}.")
    db.session.commit()
    return jsonify({"success": True, "message": "Library settings saved."}), 200


@library_bp.get("/loans")
@jwt_required()
def list_active_loans():
    if not staff_access_required():
        return denied_response()
    loans = Loan.query.filter_by(status="ACTIVE").order_by(Loan.due_date.asc()).all()
    return jsonify({"success": True, "loans": [loan.to_dict() for loan in loans]}), 200


@library_bp.get("/overdue")
@jwt_required()
def list_overdue_loans():
    if not staff_access_required():
        return denied_response()
    now = datetime.now(timezone.utc)
    loans = Loan.query.filter(Loan.status == "ACTIVE", Loan.due_date < now).order_by(Loan.due_date.asc()).all()
    records = []
    for loan in loans:
        data = loan.to_dict()
        data["late_days"] = max((now.date() - loan.due_date.date()).days, 0)
        records.append(data)
    return jsonify({"success": True, "loans": records}), 200


@library_bp.post("/loans/<int:loan_id>/return")
@jwt_required()
def return_loan(loan_id):
    if not staff_access_required():
        return denied_response()
    loan = db.session.get(Loan, loan_id)
    if not loan:
        return jsonify({"success": False, "message": "Loan was not found."}), 404
    if loan.status != "ACTIVE":
        return jsonify({"success": False, "message": "This loan has already been returned or closed."}), 409

    condition = str((request.get_json(silent=True) or {}).get("condition", "")).upper()
    if condition not in {"GOOD", "DAMAGED", "LOST"}:
        return jsonify({"success": False, "message": "Condition must be GOOD, DAMAGED, or LOST."}), 400

    returned_at = datetime.now(timezone.utc)
    late_days = max((returned_at.date() - loan.due_date.date()).days, 0)
    loan.returned_at = returned_at
    loan.return_condition = condition
    loan.status = "LOST" if condition == "LOST" else "RETURNED"
    if condition == "GOOD":
        loan.book.available_copies = min(loan.book.available_copies + 1, loan.book.total_copies)

    settings = get_library_settings()
    daily_penalty = Decimal(settings["daily_penalty"])
    penalty = None
    if late_days:
        penalty = Penalty(loan_id=loan.loan_id, user_id=loan.user_id, amount=Decimal(late_days) * daily_penalty, late_days=late_days, status="UNPAID")
        db.session.add(penalty)

    condition_message = f" The book was marked {condition.lower()}." if condition != "GOOD" else ""
    penalty_message = f" An overdue penalty of PHP {Decimal(late_days) * daily_penalty:.2f} was recorded for {late_days} late day(s)." if late_days else ""
    db.session.add(Notification(user_id=loan.user_id, title="Book return processed", message=f"Your return of '{loan.book.title}' was processed.{condition_message}{penalty_message}", category="loan"))
    record_audit(get_jwt_identity(), "BOOK_RETURNED", "LOAN", loan.loan_id, f"Returned '{loan.book.title}' ({condition}); late days: {late_days}; penalty: PHP {Decimal(late_days) * daily_penalty:.2f}.")
    db.session.commit()
    return jsonify({"success": True, "message": "Return processed.", "loan": loan.to_dict(), "late_days": late_days, "penalty_amount": float(penalty.amount) if penalty else 0}), 200


@library_bp.get("/penalties")
@jwt_required()
def list_penalties():
    if not staff_access_required():
        return denied_response()
    status = str(request.args.get("status", "ALL")).upper()
    query = Penalty.query.order_by(Penalty.created_at.desc())
    if status in {"UNPAID", "PAID"}:
        query = query.filter_by(status=status)
    return jsonify({"success": True, "penalties": [item.to_dict() for item in query.all()]}), 200


@library_bp.patch("/penalties/<int:penalty_id>/pay")
@jwt_required()
def mark_penalty_paid(penalty_id):
    if not staff_access_required():
        return denied_response()
    penalty = db.session.get(Penalty, penalty_id)
    if not penalty:
        return jsonify({"success": False, "message": "Penalty was not found."}), 404
    if penalty.status == "PAID":
        return jsonify({"success": False, "message": "Penalty is already marked paid."}), 409
    penalty.status = "PAID"
    penalty.paid_at = datetime.now(timezone.utc)
    record_audit(get_jwt_identity(), "PENALTY_PAID", "PENALTY", penalty.penalty_id, f"Collected PHP {float(penalty.amount):.2f} from {penalty.user.full_name}.")
    db.session.commit()
    return jsonify({"success": True, "message": "Penalty marked paid.", "penalty": penalty.to_dict()}), 200


@library_bp.get("/borrowers")
@jwt_required()
def list_borrowers():
    if not staff_access_required():
        return denied_response()
    users = User.query.filter(User.role.in_(["STUDENT", "TEACHER"])).order_by(User.full_name.asc()).all()
    borrowers = []
    for user in users:
        profile = user.borrower_profile
        borrowers.append({
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "account_status": user.account_status,
            "school_id_number": (profile.school_id_number if profile else None) or user.school_id,
            "course": profile.course if profile else user.course,
            "year_level": profile.year_level if profile else None,
            "section": profile.section if profile else None,
            "department": profile.department if profile else None,
            "verification_status": profile.verification_status if profile else "NO_PROFILE",
        })
    return jsonify({"success": True, "borrowers": borrowers}), 200


@library_bp.post("/notifications")
@jwt_required()
def send_notification():
    if not staff_access_required():
        return denied_response()
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    message = str(data.get("message", "")).strip()
    audience = str(data.get("audience", "ALL")).upper()
    if not title or not message:
        return jsonify({"success": False, "message": "Title and message are required."}), 400
    if audience not in {"ALL", "STUDENT", "TEACHER"}:
        return jsonify({"success": False, "message": "Audience must be ALL, STUDENT, or TEACHER."}), 400

    query = User.query.filter(User.role.in_(["STUDENT", "TEACHER"]))
    if audience in {"STUDENT", "TEACHER"}:
        query = query.filter_by(role=audience)
    recipients = query.all()
    for user in recipients:
        db.session.add(Notification(user_id=user.user_id, title=title, message=message, category="library"))
    record_audit(get_jwt_identity(), "NOTIFICATION_SENT", "NOTIFICATION", None, f"Sent '{title}' to {len(recipients)} borrower(s), audience {audience}.")
    db.session.commit()
    return jsonify({"success": True, "message": f"Notification sent to {len(recipients)} user(s).", "recipient_count": len(recipients)}), 201


@library_bp.get("/reports/summary")
@jwt_required()
def reports_summary():
    if not staff_access_required():
        return denied_response()
    return jsonify({
        "success": True,
        "total_books": db.session.query(func.coalesce(func.sum(Book.total_copies), 0)).scalar(),
        "available_books": db.session.query(func.coalesce(func.sum(Book.available_copies), 0)).scalar(),
        "borrowed_books": Loan.query.filter_by(status="ACTIVE").count(),
        "pending_requests": BorrowRequest.query.filter_by(status="PENDING").count(),
        "approved_requests": BorrowRequest.query.filter_by(status="APPROVED").count(),
        "overdue_books": Loan.query.filter(Loan.status == "ACTIVE", Loan.due_date < datetime.now(timezone.utc)).count(),
        "borrowers": User.query.filter(User.role.in_(["STUDENT", "TEACHER"])).count(),
        "unpaid_penalties": float(db.session.query(func.coalesce(func.sum(Penalty.amount), 0)).filter(Penalty.status == "UNPAID").scalar()),
    }), 200
