from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.user import User


def record_audit(actor_id, action, entity_type, entity_id, details):
    actor = db.session.get(User, actor_id) if actor_id is not None else None
    db.session.add(AuditLog(
        actor_user_id=actor.user_id if actor else None,
        actor_name=actor.full_name if actor else "Staff Registration",
        actor_role=actor.role if actor else "SYSTEM",
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details[:500],
    ))
