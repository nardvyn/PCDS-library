from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.borrow_request import BorrowRequest
from app.models.loan import Loan
from app.models.notification import Notification
from app.models.library_setting import LibrarySetting
from app.models.user import User
from app.models.library_setting import LibrarySetting

borrower_bp = Blueprint("borrower", __name__, url_prefix="/api/borrower")


@borrower_bp.get("/dashboard")
@jwt_required()
def borrower_dashboard():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User account was not found."}), 404

    now = datetime.now(timezone.utc)
    active_loans = Loan.query.filter_by(user_id=user_id, status="ACTIVE").order_by(Loan.due_date.asc()).all()
    returned_loans = Loan.query.filter(Loan.user_id == user_id, Loan.returned_at.isnot(None)).order_by(Loan.returned_at.desc()).all()
    requests = BorrowRequest.query.filter_by(user_id=user_id).order_by(BorrowRequest.requested_at.desc()).limit(5).all()
    pending_requests = BorrowRequest.query.filter_by(user_id=user_id, status="PENDING").count()
    overdue_books = Loan.query.filter(Loan.user_id == user_id, Loan.status == "ACTIVE", Loan.due_date < now).count()
    unread_notifications = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    profile = user.borrower_profile
    school_id_image_available = bool(
        profile
        and profile.school_id_image
        and (Path(current_app.config["UPLOAD_FOLDER"]) / profile.school_id_image).is_file()
    )
    settings = {row.setting_key: row.setting_value for row in LibrarySetting.query.all()}
    default_loan_days = 14 if user.role == "TEACHER" else 7
    borrowing_period = int(settings.get("teacher_loan_days" if user.role == "TEACHER" else "student_loan_days", default_loan_days))
    daily_penalty = float(settings.get("daily_penalty", "10.00"))

    return jsonify({
        "success": True,
        "borrowed_books": len(active_loans),
        "pending_requests": pending_requests,
        "overdue_books": overdue_books,
        "returned_books": len(returned_loans),
        "unread_notifications": unread_notifications,
        "verification_status": profile.verification_status if profile else "PENDING_VERIFICATION",
        "school_id_image_available": school_id_image_available,
        "borrowing_period": borrowing_period,
        "daily_penalty": daily_penalty,
        "active_loans": [loan.to_dict() for loan in active_loans],
        "recent_returns": [loan.to_dict() for loan in returned_loans[:5]],
        "recent_requests": [item.to_dict() for item in requests],
    }), 200
