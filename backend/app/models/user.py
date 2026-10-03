from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    course = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(150), unique=True, nullable=True, index=True)
    email = db.Column(db.String(150), unique=True, nullable=True, index=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    role = db.Column(
        db.Enum(
            "STUDENT",
            "TEACHER",
            "LIBRARIAN",
            "ADMIN",
            name="user_roles",
        ),
        nullable=False,
        default="STUDENT",
    )
    account_status = db.Column(
        db.Enum("ACTIVE", "INACTIVE", "SUSPENDED", name="account_statuses"),
        nullable=False,
        default="ACTIVE",
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "school_id": self.school_id,
            "full_name": self.full_name,
            "course": self.course,
            "address": self.address,
            "contact_number": self.contact_number,
            "google_id": self.google_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_picture": self.profile_picture,
            "role": self.role,
            "account_status": self.account_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
