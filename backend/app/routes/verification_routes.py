from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.borrow_request import BorrowRequest
from app.models.borrower_profile import BorrowerProfile
from app.models.notification import Notification
from app.models.user import User
from app.services.audit_service import record_audit

verification_bp = Blueprint("verification", __name__, url_prefix="/api/verification")


def is_admin():
    return get_jwt().get("role") == "ADMIN"


def borrower_profile_is_complete(profile, role):
    required_fields = (
        profile
        and profile.school_id_number
        and profile.contact_number
        and (all((profile.course, profile.year_level, profile.section)) if role == "STUDENT" else profile.department)
    )
    if not required_fields or not profile.school_id_image:
        return False
    image_path = Path(current_app.config["UPLOAD_FOLDER"]) / profile.school_id_image
    return image_path.is_file()


@verification_bp.get("/profiles")
@jwt_required()
def list_profiles():
    if not is_admin():
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    profiles = []
    for user in users:
        profile = user.borrower_profile
        profile_data = profile.to_dict() if profile else {
            "profile_id": None,
            "school_id_number": user.school_id,
            "course": user.course,
            "year_level": None,
            "section": None,
            "department": None,
            "contact_number": user.contact_number,
            "address": user.address,
            "school_id_image": None,
            "verification_status": "NO_PROFILE",
            "verified_by": None,
            "verified_at": None,
        }
        profiles.append({
            **profile_data,
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "role": user.role,
            "account_status": user.account_status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "profile_complete": borrower_profile_is_complete(profile, user.role) if user.role in {"STUDENT", "TEACHER"} else False,
            "school_id_image_available": bool(
                profile
                and profile.school_id_image
                and (Path(current_app.config["UPLOAD_FOLDER"]) / profile.school_id_image).is_file()
            ),
        })
    return jsonify({"success": True, "profiles": profiles}), 200


@verification_bp.patch("/profiles/<int:profile_id>")
@jwt_required()
def update_profile_status(profile_id):
    if not is_admin():
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    profile = db.session.get(BorrowerProfile, profile_id)
    if not profile:
        return jsonify({"success": False, "message": "Profile was not found."}), 404
    status = str((request.get_json(silent=True) or {}).get("status", "")).upper()
    if status not in {"VERIFIED", "REJECTED", "SUSPENDED"}:
        return jsonify({"success": False, "message": "Invalid verification status."}), 400
    if status == "VERIFIED" and not borrower_profile_is_complete(profile, profile.user.role):
        return jsonify({
            "success": False,
            "message": "The borrower profile is incomplete or its School ID image is unavailable. Ask the borrower to resubmit the profile before verifying.",
        }), 409
    profile.verification_status = status
    profile.verified_by = int(get_jwt_identity())
    profile.verified_at = datetime.now(timezone.utc)
    profile.user.account_status = "SUSPENDED" if status == "SUSPENDED" else "ACTIVE"
    notification_details = {
        "VERIFIED": ("School profile verified", "Your school profile has been verified. You can now submit borrow requests."),
        "REJECTED": ("School profile rejected", "Your school profile was rejected. Please contact the library for next steps."),
        "SUSPENDED": ("Account suspended", "Your library account has been suspended. Please contact the library for assistance."),
    }
    title, message = notification_details[status]
    db.session.add(Notification(user_id=profile.user_id, title=title, message=message, category="account"))
    record_audit(get_jwt_identity(), f"BORROWER_{status}", "USER", profile.user_id, f"{profile.user.full_name} ({profile.school_id_number or 'no school ID'}).")
    db.session.commit()
    return jsonify({"success": True, "message": f"Profile {status.lower()}.", "profile": profile.to_dict()}), 200


@verification_bp.get("/profiles/<int:profile_id>/school-id")
@jwt_required()
def school_id_image(profile_id):
    if not is_admin():
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    profile = db.session.get(BorrowerProfile, profile_id)
    if not profile or not profile.school_id_image:
        return jsonify({"success": False, "message": "School ID image was not found."}), 404
    image_path = Path(current_app.config["UPLOAD_FOLDER"]) / profile.school_id_image
    if not image_path.is_file():
        return jsonify({"success": False, "message": "School ID image is unavailable."}), 404
    return send_file(image_path)


@verification_bp.delete("/users/<int:user_id>")
@jwt_required()
def delete_borrower(user_id):
    if not is_admin():
        return jsonify({"success": False, "message": "Administrator access is required."}), 403
    if user_id == int(get_jwt_identity()):
        return jsonify({"success": False, "message": "You cannot delete your own account."}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User was not found."}), 404
    if user.role not in {"STUDENT", "TEACHER"}:
        return jsonify({"success": False, "message": "Only student or teacher borrower accounts can be deleted here."}), 403
    if BorrowRequest.query.filter_by(user_id=user.user_id, status="APPROVED").first():
        return jsonify({"success": False, "message": "This borrower has approved book requests. Suspend the account instead to preserve borrowing records."}), 409

    profile = user.borrower_profile
    image_name = profile.school_id_image if profile else None
    record_audit(get_jwt_identity(), "BORROWER_DELETED", "USER", user.user_id, f"Deleted {user.full_name} ({user.school_id or user.email or 'unknown ID'}).")
    db.session.query(BorrowRequest).filter_by(user_id=user.user_id).delete(synchronize_session=False)
    db.session.query(Notification).filter_by(user_id=user.user_id).delete(synchronize_session=False)
    if profile:
        db.session.delete(profile)
    db.session.delete(user)
    db.session.commit()

    if image_name:
        image_path = Path(current_app.config["UPLOAD_FOLDER"]) / image_name
        image_path.unlink(missing_ok=True)
    return jsonify({"success": True, "message": "Borrower account and its uploaded ID were deleted."}), 200
