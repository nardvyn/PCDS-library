from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.get("")
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    items = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify({
        "success": True,
        "notifications": [item.to_dict() for item in items],
        "unread_count": sum(not item.is_read for item in items),
    }), 200


@notifications_bp.patch("/<int:notification_id>/read")
@jwt_required()
def mark_notification_read(notification_id):
    user_id = int(get_jwt_identity())
    item = Notification.query.filter_by(notification_id=notification_id, user_id=user_id).first()
    if not item:
        return jsonify({"success": False, "message": "Notification was not found."}), 404
    item.is_read = True
    db.session.commit()
    return jsonify({"success": True, "message": "Notification marked as read."}), 200
