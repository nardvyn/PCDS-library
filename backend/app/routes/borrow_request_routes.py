from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.book import Book
from app.models.borrow_request import BorrowRequest
from app.models.borrower_profile import BorrowerProfile
from app.models.notification import Notification
from app.models.loan import Loan
from app.models.library_setting import LibrarySetting
from app.models.user import User
from app.services.audit_service import record_audit

borrow_requests_bp = Blueprint("borrow_requests", __name__, url_prefix="/api/borrow-requests")


def has_staff_access():
    return get_jwt().get("role") in {"ADMIN", "LIBRARIAN"}


@borrow_requests_bp.get("")
@jwt_required()
def list_borrow_requests():
    if not has_staff_access():
        return jsonify({"success": False, "message": "Staff access is required."}), 403
    status = str(request.args.get("status", "PENDING")).upper()
    query = BorrowRequest.query.order_by(BorrowRequest.requested_at.desc())
    if status != "ALL":
        query = query.filter_by(status=status)
    return jsonify({"success": True, "requests": [item.to_dict() for item in query.all()]}), 200


@borrow_requests_bp.post("")
@jwt_required()
def create_borrow_request():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or user.account_status != "ACTIVE":
        return jsonify({"success": False, "message": "Your library account is suspended or inactive. Borrow requests are disabled."}), 403
    role = user.role
    if role not in {"STUDENT", "TEACHER"}:
        return jsonify({"success": False, "message": "Only students and teachers can request books."}), 403

    data = request.form if request.files else (request.get_json(silent=True) or {})
    profile = BorrowerProfile.query.filter_by(user_id=user_id).first()
    if not profile or profile.verification_status != "VERIFIED":
        return jsonify({"success": False, "message": "Your school profile must be verified before borrowing books."}), 403

    book_id = str(data.get("book_id", "")).strip()
    if book_id:
        book = db.session.get(Book, int(book_id))
        if not book or not book.is_active or book.available_copies < 1:
            return jsonify({"success": False, "message": "The selected book is unavailable."}), 404
        duplicate = BorrowRequest.query.filter_by(user_id=user_id, book_id=book.book_id, status="PENDING").first()
        if duplicate:
            return jsonify({"success": False, "message": "You already have a pending request for this book."}), 409
        item = BorrowRequest(user_id=user_id, book_id=book.book_id)
        db.session.add(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Borrow request submitted.", "request": item.to_dict()}), 201

    requested_title = str(data.get("title", "")).strip()
    requested_author = str(data.get("author", "")).strip() or None
    call_number = str(data.get("call_number", "")).strip()
    accession_number = str(data.get("accession_number", "")).strip()
    image = request.files.get("book_image")
    if not requested_title or not call_number or not accession_number or not image or not image.filename:
        return jsonify({"success": False, "message": "Book title, call number, accession number, and a book photo are required."}), 400
    extension = Path(image.filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify({"success": False, "message": "Only JPG, PNG, and WebP book photos are allowed."}), 400

    duplicate = BorrowRequest.query.filter_by(user_id=user_id, accession_number=accession_number, status="PENDING").first()
    if duplicate:
        return jsonify({"success": False, "message": "You already have a pending request for this accession number."}), 409

    matched_book = Book.query.filter_by(accession_number=accession_number).first()
    if matched_book and matched_book.available_copies < 1:
        return jsonify({"success": False, "message": "This accession number currently has no available copies."}), 409
    filename = secure_filename(f"request-{user_id}-{uuid4().hex}{extension}")
    image_folder = Path(current_app.config["UPLOAD_FOLDER"]).parent / "borrow_request_books"
    image_folder.mkdir(parents=True, exist_ok=True)
    image_path = image_folder / filename
    image.save(image_path)
    item = BorrowRequest(
        user_id=user_id,
        book_id=matched_book.book_id if matched_book else None,
        requested_title=requested_title,
        requested_author=requested_author,
        call_number=call_number,
        accession_number=accession_number,
        book_image=filename,
    )
    db.session.add(item)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        image_path.unlink(missing_ok=True)
        return jsonify({"success": False, "message": "Unable to submit the borrow request."}), 500
    return jsonify({"success": True, "message": "Borrow request submitted.", "request": item.to_dict()}), 201


@borrow_requests_bp.get("/<int:request_id>/book-image")
@jwt_required()
def borrow_request_book_image(request_id):
    if not has_staff_access():
        return jsonify({"success": False, "message": "Staff access is required."}), 403
    item = db.session.get(BorrowRequest, request_id)
    if not item or not item.book_image:
        return jsonify({"success": False, "message": "Book image was not found."}), 404
    image_path = Path(current_app.config["UPLOAD_FOLDER"]).parent / "borrow_request_books" / item.book_image
    if not image_path.is_file():
        return jsonify({"success": False, "message": "Book image is unavailable."}), 404
    return send_file(image_path)


@borrow_requests_bp.patch("/<int:request_id>")
@jwt_required()
def update_borrow_request(request_id):
    if not has_staff_access():
        return jsonify({"success": False, "message": "Staff access is required."}), 403

    item = db.session.get(BorrowRequest, request_id)
    if not item:
        return jsonify({"success": False, "message": "Borrow request was not found."}), 404

    status = str((request.get_json(silent=True) or {}).get("status", "")).upper()
    if status not in {"APPROVED", "REJECTED"}:
        return jsonify({"success": False, "message": "Status must be APPROVED or REJECTED."}), 400
    if item.status != "PENDING":
        return jsonify({"success": False, "message": "This request has already been processed."}), 409
    book = item.book
    if status == "APPROVED" and book is None:
        book = Book.query.filter_by(accession_number=item.accession_number).first()
        if book is None:
            book = Book(
                title=item.requested_title or "Untitled requested book",
                author=item.requested_author or "Unknown author",
                call_number=item.call_number,
                accession_number=item.accession_number or f"REQ-{item.request_id}",
                cover_image=item.book_image,
                total_copies=1,
                available_copies=1,
            )
            db.session.add(book)
            db.session.flush()
        item.book = book
    if status == "APPROVED" and book.available_copies < 1:
        return jsonify({"success": False, "message": "The book no longer has available copies."}), 409

    item.status = status
    item.processed_at = datetime.now(timezone.utc)
    if status == "APPROVED":
        book.available_copies -= 1
        book.is_active = True
        borrowed_at = datetime.now(timezone.utc)
        settings = {row.setting_key: row.setting_value for row in LibrarySetting.query.all()}
        default_days = 14 if item.user.role == "TEACHER" else 7
        loan_days = int(settings.get("teacher_loan_days" if item.user.role == "TEACHER" else "student_loan_days", default_days))
        due_date = borrowed_at + timedelta(days=loan_days)
        db.session.add(Loan(request_id=item.request_id, user_id=item.user_id, book_id=book.book_id, borrowed_at=borrowed_at, due_date=due_date, status="ACTIVE"))
        title = "Borrow request approved"
        message = f"Your request for '{book.title}' was approved. Return it by {due_date.strftime('%B %d, %Y')} ({loan_days}-day loan)."
    else:
        title = "Borrow request rejected"
        message = f"Your request for '{item.book.title if item.book else item.requested_title}' was rejected. Please contact the library if you need more information."
    db.session.add(Notification(user_id=item.user_id, title=title, message=message, category="borrow_request"))
    record_audit(get_jwt_identity(), f"BORROW_REQUEST_{status}", "BORROW_REQUEST", item.request_id, f"{item.book.title if item.book else item.requested_title} requested by {item.user.full_name}.")
    db.session.commit()
    return jsonify({"success": True, "message": f"Request {status.lower()}.", "request": item.to_dict()}), 200
