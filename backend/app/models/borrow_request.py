from datetime import datetime, timezone

from app.extensions import db


class BorrowRequest(db.Model):
    __tablename__ = "borrow_requests"

    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=True, index=True)
    requested_title = db.Column(db.String(200), nullable=True)
    requested_author = db.Column(db.String(150), nullable=True)
    call_number = db.Column(db.String(50), nullable=True)
    accession_number = db.Column(db.String(50), nullable=True, index=True)
    book_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Enum("PENDING", "APPROVED", "REJECTED", name="borrow_request_statuses"), nullable=False, default="PENDING")
    requested_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")
    book = db.relationship("Book")

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "borrower_name": self.user.full_name if self.user else "Unknown borrower",
            "school_id": self.user.school_id if self.user else "",
            "book_id": self.book_id,
            "book_title": self.book.title if self.book else (self.requested_title or "Unknown book"),
            "author": (self.book.author if self.book else None) or (self.requested_author or ""),
            "call_number": (self.book.call_number if self.book else None) or (self.call_number or ""),
            "accession_number": (self.book.accession_number if self.book else None) or (self.accession_number or ""),
            "has_book_image": bool(self.book_image or (self.book and self.book.cover_image)),
            "status": self.status,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
