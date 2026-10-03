from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import or_

from app.extensions import db
from app.models.book import Book
from app.services.audit_service import record_audit

books_bp = Blueprint("books", __name__, url_prefix="/api/books")


def can_manage_books():
    return get_jwt().get("role") in {"LIBRARIAN", "ADMIN"}


@books_bp.get("")
@jwt_required()
def list_books():
    search = str(request.args.get("search", "")).strip()
    query = Book.query.filter_by(is_active=True).order_by(Book.title.asc())
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Book.title.ilike(pattern), Book.author.ilike(pattern), Book.isbn.ilike(pattern), Book.accession_number.ilike(pattern), Book.call_number.ilike(pattern)))
    return jsonify({"success": True, "books": [book.to_dict() for book in query.all()]}), 200


@books_bp.get("/<int:book_id>/cover-image")
@jwt_required()
def get_book_cover_image(book_id):
    if not can_manage_books():
        return jsonify({"success": False, "message": "Librarian or administrator access is required."}), 403
    book = db.session.get(Book, book_id)
    if not book or not book.cover_image or Path(book.cover_image).name != book.cover_image:
        return jsonify({"success": False, "message": "Book cover image was not found."}), 404
    image_path = Path(current_app.config["UPLOAD_FOLDER"]).parent / "borrow_request_books" / book.cover_image
    if not image_path.is_file():
        return jsonify({"success": False, "message": "Book cover image is unavailable."}), 404
    return send_file(image_path)


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
