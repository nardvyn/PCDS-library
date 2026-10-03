from datetime import datetime, timezone

from app.extensions import db


class Penalty(db.Model):
    __tablename__ = "penalties"

    penalty_id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.loan_id"), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    late_days = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("UNPAID", "PAID", name="penalty_statuses"), nullable=False, default="UNPAID", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    paid_at = db.Column(db.DateTime, nullable=True)

    loan = db.relationship("Loan")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "penalty_id": self.penalty_id,
            "loan_id": self.loan_id,
            "user_id": self.user_id,
            "borrower_name": self.user.full_name if self.user else "Unknown borrower",
            "school_id": self.user.school_id if self.user else "",
            "book_title": self.loan.book.title if self.loan and self.loan.book else "Unknown book",
            "amount": float(self.amount),
            "late_days": self.late_days,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }
