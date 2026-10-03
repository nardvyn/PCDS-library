from datetime import datetime, timezone

from app.extensions import db


class Book(db.Model):
    __tablename__ = "books"

    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False)
    call_number = db.Column(db.String(50), nullable=True)
    isbn = db.Column(db.String(30), nullable=True, unique=True)
    accession_number = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=True)
    publication_year = db.Column(db.Integer, nullable=True)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "call_number": self.call_number,
            "isbn": self.isbn,
            "accession_number": self.accession_number,
            "category": self.category,
            "publication_year": self.publication_year,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "description": self.description,
            "cover_image": self.cover_image,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
