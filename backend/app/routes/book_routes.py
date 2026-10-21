from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.book import Book
from app.models.borrow_request import BorrowRequest
from app.services.audit_service import record_audit

books_bp = Blueprint("books", __name__, url_prefix="/api/books")
ALLOWED_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_COVER_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_COVER_BYTES = 5 * 1024 * 1024


def can_manage_books():
    return get_jwt().get("role") in {"LIBRARIAN", "ADMIN"}


def cover_image_path(filename):
    if not filename or Path(filename).name != filename:
        return None
    uploads_root = Path(current_app.config["UPLOAD_FOLDER"]).parent
    for folder in ("book_covers", "borrow_request_books"):
        candidate = uploads_root / folder / filename
        if candidate.is_file():
            return candidate
    return None


@books_bp.get("")
@jwt_required()
def list_books():
    search = str(request.args.get("search", "")).strip()
    query = Book.query.filter_by(is_active=True).order_by(Book.title.asc())
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            Book.title.ilike(pattern),
            Book.author.ilike(pattern),
            Book.isbn.ilike(pattern),
            Book.accession_number.ilike(pattern),
            Book.call_number.ilike(pattern),
            Book.category.ilike(pattern),
            Book.description.ilike(pattern),
        ))
    return jsonify({"success": True, "books": [book.to_dict() for book in query.all()]}), 200


@books_bp.get("/<int:book_id>/cover-image")
@jwt_required()
def get_book_cover_image(book_id):
    book = db.session.get(Book, book_id)
    if not book or not book.is_active:
        return jsonify({"success": False, "message": "Book cover image was not found."}), 404
    image_path = cover_image_path(book.cover_image)
    if not image_path:
        return jsonify({"success": False, "message": "Book cover image is unavailable."}), 404
    return send_file(image_path)


@books_bp.post("/<int:book_id>/cover-image")
@jwt_required()
def upload_book_cover_image(book_id):
    if not can_manage_books():
        return jsonify({"success": False, "message": "Librarian or administrator access is required."}), 403

    book = db.session.get(Book, book_id)
    image = request.files.get("cover_image")
    if not book or not book.is_active:
        return jsonify({"success": False, "message": "Book was not found in the active catalog."}), 404
    if not image or not image.filename:
        return jsonify({"success": False, "message": "Choose a book cover image to upload."}), 400

    extension = Path(image.filename).suffix.lower()
    if extension not in ALLOWED_COVER_EXTENSIONS or image.mimetype not in ALLOWED_COVER_MIME_TYPES:
        return jsonify({"success": False, "message": "Only JPG, PNG, and WebP cover images are allowed."}), 400

    image.stream.seek(0, 2)
    image_size = image.stream.tell()
    image.stream.seek(0)
    if image_size <= 0 or image_size > MAX_COVER_BYTES:
        return jsonify({"success": False, "message": "The cover image must be no larger than 5 MB."}), 413

    filename = secure_filename(f"book-{book_id}-{uuid4().hex}{extension}")
    image_folder = Path(current_app.config["UPLOAD_FOLDER"]).parent / "book_covers"
    image_folder.mkdir(parents=True, exist_ok=True)
    image_path = image_folder / filename
    previous_image = book.cover_image
    image.save(image_path)
    book.cover_image = filename
    try:
        record_audit(get_jwt_identity(), "BOOK_COVER_UPDATED", "BOOK", book.book_id, f"Updated the cover image for '{book.title}'.")
        db.session.commit()
    except Exception:
        db.session.rollback()
        image_path.unlink(missing_ok=True)
        return jsonify({"success": False, "message": "Unable to save the book cover image."}), 500

    previous_path = cover_image_path(previous_image)
    if previous_path and previous_path.parent == image_folder and previous_path.name != filename:
        previous_path.unlink(missing_ok=True)
    return jsonify({"success": True, "message": "Book cover image uploaded successfully.", "book": book.to_dict()}), 200


@books_bp.post("")
@jwt_required()
def create_book():
    if not can_manage_books():
        return jsonify({"success": False, "message": "Librarian or administrator access is required."}), 403

    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    accession_number = str(data.get("accession_number", "")).strip()
    call_number = str(data.get("call_number", "")).strip() or None
    isbn = str(data.get("isbn", "")).strip() or None

    if not title or not author or not accession_number:
        return jsonify({"success": False, "message": "Title, author, and accession number are required."}), 400

    try:
        total_copies = int(data.get("total_copies", 1))
        publication_year = data.get("publication_year")
        publication_year = int(publication_year) if publication_year not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Year and copies must be valid numbers."}), 400

    if total_copies < 1:
        return jsonify({"success": False, "message": "Copies must be at least 1."}), 400
    if publication_year is not None and (publication_year < 1000 or publication_year > 9999):
        return jsonify({"success": False, "message": "Publication year is invalid."}), 400

    if Book.query.filter_by(accession_number=accession_number).first() or (isbn and Book.query.filter_by(isbn=isbn).first()):
        return jsonify({"success": False, "message": "The accession number or ISBN already exists."}), 409

    book = Book(title=title, author=author, isbn=isbn, accession_number=accession_number, call_number=call_number, category=str(data.get("category", "")).strip() or None, publication_year=publication_year, total_copies=total_copies, available_copies=total_copies, description=str(data.get("description", "")).strip() or None)
    try:
        db.session.add(book)
        db.session.flush()
        record_audit(get_jwt_identity(), "BOOK_CREATED", "BOOK", book.book_id, f"Added '{book.title}' ({book.total_copies} copies, accession {book.accession_number}).")
        db.session.commit()
        return jsonify({"success": True, "message": "Book added successfully.", "book": book.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Unable to add the book."}), 500


@books_bp.put("/<int:book_id>")
@jwt_required()
def update_book(book_id):
    if not can_manage_books():
        return jsonify({"success": False, "message": "Librarian or administrator access is required."}), 403

    book = db.session.get(Book, book_id)
    if not book or not book.is_active:
        return jsonify({"success": False, "message": "Book was not found in the active catalog."}), 404

    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    accession_number = str(data.get("accession_number", "")).strip()
    call_number = str(data.get("call_number", "")).strip() or None
    isbn = str(data.get("isbn", "")).strip() or None
    category = str(data.get("category", "")).strip() or None
    description = str(data.get("description", "")).strip() or None

    if not title or not author or not accession_number:
        return jsonify({"success": False, "message": "Title, author, and accession number are required."}), 400
    if len(title) > 200 or len(author) > 150 or len(accession_number) > 50 or (call_number and len(call_number) > 50) or (isbn and len(isbn) > 30) or (category and len(category) > 100):
        return jsonify({"success": False, "message": "One or more book details exceed the allowed length."}), 400

    try:
        publication_year = data.get("publication_year")
        publication_year = int(publication_year) if publication_year not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Publication year must be a valid number."}), 400
    if publication_year is not None and not 1000 <= publication_year <= 9999:
        return jsonify({"success": False, "message": "Publication year is invalid."}), 400

    accession_owner = Book.query.filter(Book.accession_number == accession_number, Book.book_id != book_id).first()
    isbn_owner = Book.query.filter(Book.isbn == isbn, Book.book_id != book_id).first() if isbn else None
    if accession_owner or isbn_owner:
        return jsonify({"success": False, "message": "The accession number or ISBN already belongs to another book."}), 409

    try:
        previous_title = book.title
        book.title = title
        book.author = author
        book.accession_number = accession_number
        book.call_number = call_number
        book.isbn = isbn
        book.category = category
        book.publication_year = publication_year
        book.description = description
        record_audit(
            get_jwt_identity(),
            "BOOK_UPDATED",
            "BOOK",
            book.book_id,
            f"Updated metadata for '{previous_title}' to '{book.title}' (accession {book.accession_number}).",
        )
        db.session.commit()
        return jsonify({"success": True, "message": "Book details updated successfully.", "book": book.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Unable to update the book details."}), 500


@books_bp.delete("/<int:book_id>")
@jwt_required()
def deactivate_book(book_id):
    if not can_manage_books():
        return jsonify({"success": False, "message": "Librarian or administrator access is required."}), 403

    book = db.session.get(Book, book_id)
    if not book or not book.is_active:
        return jsonify({"success": False, "message": "Book was not found in the active catalog."}), 404

    pending_requests = BorrowRequest.query.filter_by(book_id=book_id, status="PENDING").count()
    if pending_requests:
        return jsonify({
            "success": False,
            "message": f"This book has {pending_requests} pending borrow request(s). Review them before removing it from the catalog.",
        }), 409

    try:
        book.is_active = False
        record_audit(
            get_jwt_identity(),
            "BOOK_REMOVED",
            "BOOK",
            book.book_id,
            f"Removed '{book.title}' (accession {book.accession_number}) from the active catalog.",
        )
        db.session.commit()
        return jsonify({"success": True, "message": "Book removed from the catalog. Its borrowing history has been kept."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Unable to remove the book from the catalog."}), 500
