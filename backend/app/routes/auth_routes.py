import hashlib
import hmac
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.utils import secure_filename
from pathlib import Path
from hmac import compare_digest
from uuid import uuid4
from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.borrower_profile import BorrowerProfile
from app.services.audit_service import record_audit

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
PASSWORD_RESET_MAX_AGE = 30 * 60


def password_reset_serializer():
    return URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"], salt="pcds-library-password-reset")


def password_reset_nonce(user):
    secret = str(current_app.config["JWT_SECRET_KEY"]).encode()
    password_marker = (user.password_hash or "no-password").encode()
    return hmac.new(secret, password_marker, hashlib.sha256).hexdigest()


def send_password_reset_email(recipient, reset_url):
    mail_server = current_app.config.get("MAIL_SERVER")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    if not mail_server or not sender:
        raise RuntimeError("Password reset email is not configured.")

    message = EmailMessage()
    message["Subject"] = "Reset your PCDS Library password"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your PCDS Library password. "
        f"Use this link within 30 minutes: {reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    mail_port = current_app.config.get("MAIL_PORT", 587)
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    if current_app.config.get("MAIL_USE_SSL"):
        with smtplib.SMTP_SSL(mail_server, mail_port, timeout=10, context=ssl.create_default_context()) as server:
            if username:
                server.login(username, password or "")
            server.send_message(message)
        return

    with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
        if current_app.config.get("MAIL_USE_TLS", True):
            server.starttls(context=ssl.create_default_context())
        if username:
            server.login(username, password or "")
        server.send_message(message)


def issue_token(user):
    return create_access_token(
        identity=str(user.user_id),
        additional_claims={"role": user.role, "school_id": user.school_id},
    )


@auth_bp.post("/google")
def google_login():
    credential = str((request.get_json(silent=True) or {}).get("credential", ""))
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not credential or not client_id:
        return jsonify({"success": False, "message": "Google sign-in is not configured."}), 503

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=60,
        )
    except ValueError as error:
        current_app.logger.warning("Google ID token verification failed: %s", error)
        return jsonify({
            "success": False,
            "message": "Google could not verify this sign-in. Check that the OAuth Client ID and authorized origin match.",
            "reason": str(error),
        }), 401

    if not claims.get("email_verified"):
        return jsonify({"success": False, "message": "Google email is not verified."}), 401

    google_id = claims.get("sub")
    email = str(claims.get("email", "")).lower().strip()
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "This email is already linked to another account."}), 409
        user = User(
            school_id=f"GOOGLE-{google_id[-10:]}",
            full_name=claims.get("name") or email or "Google User",
            first_name=claims.get("given_name"),
            last_name=claims.get("family_name"),
            google_id=google_id,
            email=email,
            profile_picture=claims.get("picture"),
            role="STUDENT",
            account_status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(BorrowerProfile(user_id=user.user_id))
        db.session.commit()
        profile_required = True
    else:
        user.google_id = google_id
        user.email = email
        user.profile_picture = claims.get("picture") or user.profile_picture
        db.session.commit()
        profile_required = user.borrower_profile is None or user.borrower_profile.verification_status != "VERIFIED"

    return jsonify({"success": True, "access_token": issue_token(user), "user": user.to_dict(), "profile_required": profile_required}), 200


@auth_bp.put("/profile")
@jwt_required()
def complete_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"success": False, "message": "User account was not found."}), 404
    data = request.form if request.files else (request.get_json(silent=True) or {})
    school_id = str(data.get("school_id_number", "")).strip()
    contact_number = str(data.get("contact_number", "")).strip()
    password = str(data.get("password", ""))
    user_type = str(data.get("user_type", "STUDENT")).upper()
    image = request.files.get("school_id")
    if not school_id or not contact_number or not image or not image.filename or user_type not in {"STUDENT", "TEACHER"}:
        return jsonify({"success": False, "message": "School ID, phone number, account type, and School ID photo are required."}), 400
    if not user.password_hash and len(password) < 8:
        return jsonify({"success": False, "message": "Create a password with at least 8 characters."}), 400
    course = str(data.get("course", "")).strip()
    year_level = str(data.get("year_level", "")).strip()
    section = str(data.get("section", "")).strip()
    department = str(data.get("department", "")).strip()
    if user_type == "STUDENT" and not all((course, year_level, section)):
        return jsonify({"success": False, "message": "Course, year level, and section are required for students."}), 400
    if user_type == "TEACHER" and not department:
        return jsonify({"success": False, "message": "Department is required for teachers."}), 400
    phone_digits = "".join(character for character in contact_number if character.isdigit())
    if not 7 <= len(phone_digits) <= 15 or len(contact_number) > 20:
        return jsonify({"success": False, "message": "Enter a valid phone number (7-15 digits)."}), 400
    extension = Path(image.filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify({"success": False, "message": "Only JPG, PNG, and WebP School ID images are allowed."}), 400
    if BorrowerProfile.query.filter(BorrowerProfile.school_id_number == school_id, BorrowerProfile.user_id != user.user_id).first():
        return jsonify({"success": False, "message": "That school ID is already registered."}), 409

    profile = user.borrower_profile or BorrowerProfile(user_id=user.user_id)
    previous_image = profile.school_id_image
    filename = secure_filename(f"{user.user_id}-{uuid4().hex}{extension}")
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    image_path = upload_folder / filename
    image.save(image_path)

    user.school_id = school_id
    user.contact_number = contact_number
    if not user.password_hash:
        user.set_password(password)
    profile.school_id_number = school_id
    profile.course = course or None
    profile.year_level = year_level or None
    profile.section = section or None
    profile.department = department or None
    profile.contact_number = contact_number
    profile.address = str(data.get("address", "")).strip() or None
    profile.school_id_image = filename
    profile.verification_status = "PENDING_VERIFICATION"
    user.role = user_type
    if not user.borrower_profile:
        db.session.add(profile)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        image_path.unlink(missing_ok=True)
        return jsonify({"success": False, "message": "Unable to save your complete profile."}), 500

    if previous_image and previous_image != filename:
        (upload_folder / previous_image).unlink(missing_ok=True)
    return jsonify({"success": True, "message": "Complete profile and School ID submitted for verification.", "profile": profile.to_dict(), "user": user.to_dict()}), 200


@auth_bp.post("/profile/school-id")
@jwt_required()
def upload_school_id():
    user = db.session.get(User, int(get_jwt_identity()))
    image = request.files.get("school_id")
    if not user or not image or not image.filename:
        return jsonify({"success": False, "message": "A School ID image is required."}), 400
    extension = Path(image.filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify({"success": False, "message": "Only JPG, PNG, and WebP images are allowed."}), 400
    filename = f"{user.user_id}-{uuid4().hex}{extension}"
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    image.save(upload_folder / secure_filename(filename))
    profile = user.borrower_profile or BorrowerProfile(user_id=user.user_id)
    profile.school_id_image = filename
    if not user.borrower_profile:
        db.session.add(profile)
    db.session.commit()
    return jsonify({"success": True, "message": "School ID uploaded securely.", "profile": profile.to_dict()}), 200


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required.",
        }), 400

    if "@" not in email:
        return jsonify({"success": False, "message": "Enter a valid email address."}), 400

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 8 characters.",
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "message": "The email address is already registered.",
        }), 409

    user = User(
        full_name=email.split("@")[0],
        email=email,
        role="STUDENT",
        account_status="ACTIVE",
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.flush()
        db.session.add(BorrowerProfile(user_id=user.user_id))
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "access_token": issue_token(user),
            "user": user.to_dict(),
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Unable to create the account.",
        }), 500


@auth_bp.post("/staff-register")
def staff_register():
    data = request.get_json(silent=True) or {}
    invite_code = str(data.get("invite_code", ""))
    configured_code = current_app.config.get("STAFF_REGISTRATION_CODE") or ""
    if not configured_code or not compare_digest(invite_code, configured_code):
        return jsonify({"success": False, "message": "A valid staff registration code is required."}), 403

    full_name = str(data.get("full_name", "")).strip()
    staff_id = str(data.get("staff_id", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not full_name or not staff_id or not email or not password:
        return jsonify({"success": False, "message": "Full name, staff ID, email, and password are required."}), 400
    if "@" not in email:
        return jsonify({"success": False, "message": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must contain at least 8 characters."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "The email address is already registered."}), 409
    if User.query.filter_by(school_id=staff_id).first():
        return jsonify({"success": False, "message": "The staff ID is already registered."}), 409

    staff = User(
        school_id=staff_id,
        full_name=full_name,
        first_name=full_name.split()[0],
        last_name=" ".join(full_name.split()[1:]) or None,
        email=email,
        role="LIBRARIAN",
        account_status="ACTIVE",
    )
    staff.set_password(password)
    try:
        db.session.add(staff)
        db.session.flush()
        record_audit(None, "LIBRARIAN_REGISTERED", "USER", staff.user_id, f"Registered librarian {staff.full_name} ({staff.email}).")
        db.session.commit()
        return jsonify({"success": True, "message": "Librarian account created. You can now sign in."}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Unable to create the staff account."}), 500


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    identifier = str(data.get("email", data.get("identifier", ""))).strip()
    email = identifier.lower()
    password = str(data.get("password", ""))

    if not identifier or not password:
        return jsonify({
            "success": False,
            "message": "Staff email or ID and password are required.",
        }), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User.query.filter(func.lower(User.school_id) == identifier.lower()).first()
    if user and not user.password_hash and user.google_id:
        return jsonify({
            "success": False,
            "message": "This account uses Google sign-in. Continue with Google.",
        }), 401

    if not user or not user.check_password(password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password.",
        }), 401

    if user.account_status != "ACTIVE":
        return jsonify({
            "success": False,
            "message": "Your account is not active.",
        }), 403

    access_token = create_access_token(
        identity=str(user.user_id),
        additional_claims={
            "role": user.role,
            "school_id": user.school_id,
            "email": user.email,
        },
    )
    return jsonify({
        "success": True,
        "message": "Login successful.",
        "access_token": access_token,
        "user": user.to_dict(),
        "next_page": "/dashboard" if user.borrower_profile and user.borrower_profile.verification_status == "VERIFIED" else "/dashboard",
    }), 200


@auth_bp.post("/forgot-password")
def forgot_password():
    email = str((request.get_json(silent=True) or {}).get("email", "")).strip().lower()
    if not email or "@" not in email or len(email) > 150:
        return jsonify({"success": False, "message": "Enter a valid email address."}), 400
    if not current_app.config.get("MAIL_SERVER") or not current_app.config.get("MAIL_DEFAULT_SENDER"):
        return jsonify({"success": False, "message": "Password reset email is not configured. Contact the library administrator."}), 503

    user = User.query.filter_by(email=email).first()
    if user:
        token = password_reset_serializer().dumps({"user_id": user.user_id, "nonce": password_reset_nonce(user)})
        reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password?{urlencode({'token': token})}"
        try:
            send_password_reset_email(user.email, reset_url)
        except Exception:
            current_app.logger.exception("Unable to deliver a password reset email.")

    return jsonify({"success": True, "message": "If an account exists for that email, a password reset link will be sent."}), 200


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = str(data.get("token", ""))
    password = str(data.get("password", ""))
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must contain at least 8 characters."}), 400

    try:
        payload = password_reset_serializer().loads(token, max_age=PASSWORD_RESET_MAX_AGE)
        user_id = int(payload.get("user_id", 0))
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return jsonify({"success": False, "message": "This password reset link is invalid or has expired. Request a new one."}), 400

    user = db.session.get(User, user_id)
    if not user or not hmac.compare_digest(str(payload.get("nonce", "")), password_reset_nonce(user)):
        return jsonify({"success": False, "message": "This password reset link is invalid or has expired. Request a new one."}), 400

    user.set_password(password)
    db.session.commit()
    return jsonify({"success": True, "message": "Your password has been reset. You can now sign in."}), 200


@auth_bp.get("/me")
@jwt_required()
def current_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({
            "success": False,
            "message": "User account was not found.",
        }), 404

    return jsonify({"success": True, "user": user.to_dict()}), 200


@auth_bp.put("/email")
@jwt_required()
def update_account_email():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"success": False, "message": "User account was not found."}), 404
    if user.google_id:
        return jsonify({"success": False, "message": "This email is managed by your Google account."}), 403

    email = str((request.get_json(silent=True) or {}).get("email", "")).strip().lower()
    if "@" not in email or len(email) > 150:
        return jsonify({"success": False, "message": "Enter a valid email address."}), 400
    existing_user = User.query.filter(User.email == email, User.user_id != user.user_id).first()
    if existing_user:
        return jsonify({"success": False, "message": "That email address is already in use."}), 409
    if email == user.email:
        return jsonify({"success": True, "message": "Email address is unchanged.", "user": user.to_dict()}), 200

    previous_email = user.email
    user.email = email
    record_audit(user.user_id, "ACCOUNT_EMAIL_UPDATED", "USER", user.user_id, f"Changed account email from {previous_email} to {email}.")
    db.session.commit()
    return jsonify({"success": True, "message": "Email address updated. Use the new email next time you sign in.", "user": user.to_dict()}), 200
