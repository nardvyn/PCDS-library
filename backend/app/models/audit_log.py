from datetime import datetime, timezone

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    audit_log_id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    actor_name = db.Column(db.String(150), nullable=False)
    actor_role = db.Column(db.String(30), nullable=False)
    action = db.Column(db.String(60), nullable=False, index=True)
    entity_type = db.Column(db.String(60), nullable=False)
    entity_id = db.Column(db.String(80), nullable=True)
    details = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    actor = db.relationship("User", foreign_keys=[actor_user_id])

    def to_dict(self):
        return {
            "audit_log_id": self.audit_log_id,
            "actor_user_id": self.actor_user_id,
            "actor_name": self.actor_name,
            "actor_role": self.actor_role,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
