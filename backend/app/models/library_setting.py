from datetime import datetime, timezone

from app.extensions import db


class LibrarySetting(db.Model):
    __tablename__ = "library_settings"

    setting_key = db.Column(db.String(80), primary_key=True)
    setting_value = db.Column(db.String(120), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
