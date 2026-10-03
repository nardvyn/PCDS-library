from datetime import datetime, timezone

from app.extensions import db


class BorrowerProfile(db.Model):
    __tablename__ = "borrower_profiles"

    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False)
    school_id_number = db.Column(db.String(50), nullable=True, unique=True)
    course = db.Column(db.String(100), nullable=True)
    year_level = db.Column(db.String(30), nullable=True)
    section = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    school_id_image = db.Column(db.String(255), nullable=True)
    verification_status = db.Column(db.Enum("PENDING_VERIFICATION", "VERIFIED", "REJECTED", "SUSPENDED", name="verification_statuses"), nullable=False, default="PENDING_VERIFICATION")
    verified_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("borrower_profile", uselist=False))

    def to_dict(self):
        return {
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "school_id_number": self.school_id_number,
            "course": self.course,
            "year_level": self.year_level,
            "section": self.section,
            "department": self.department,
            "contact_number": self.contact_number,
            "address": self.address,
            "school_id_image": self.school_id_image,
            "verification_status": self.verification_status,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }
