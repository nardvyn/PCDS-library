from datetime import datetime, timezone

from app.extensions import db


class Loan(db.Model):
    __tablename__ = "loans"

    loan_id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("borrow_requests.request_id"), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False, index=True)
    borrowed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum("ACTIVE", "RETURNED", "LOST", name="loan_statuses"), nullable=False, default="ACTIVE", index=True)
    return_condition = db.Column(db.Enum("GOOD", "DAMAGED", "LOST", name="return_conditions"), nullable=True)

    request = db.relationship("BorrowRequest", backref=db.backref("loan", uselist=False))
    user = db.relationship("User")
    book = db.relationship("Book")

    def to_dict(self):
        profile = self.user.borrower_profile if self.user else None
        return {
            "loan_id": self.loan_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "borrower_name": self.user.full_name if self.user else "Unknown borrower",
            "school_id": (profile.school_id_number if profile else None) or (self.user.school_id if self.user else ""),
            "role": self.user.role if self.user else "",
            "book_id": self.book_id,
            "book_title": self.book.title if self.book else "Unknown book",
            "accession_number": self.book.accession_number if self.book else "",
            "borrowed_at": self.borrowed_at.isoformat() if self.borrowed_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "status": self.status,
            "return_condition": self.return_condition,
        }
