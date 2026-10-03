from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from app.models.audit_log import AuditLog

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit-logs")


@audit_bp.get("")
@jwt_required()
def list_audit_logs():
    if get_jwt().get("role") != "ADMIN":
        return jsonify({"success": False, "message": "Administrator access is required."}), 403

    try:
        limit = min(max(int(request.args.get("limit", 300)), 1), 500)
    except (TypeError, ValueError):
        limit = 300
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return jsonify({"success": True, "logs": [item.to_dict() for item in logs]}), 200
