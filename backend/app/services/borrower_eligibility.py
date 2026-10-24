from datetime import datetime, timezone


STUDENT_VERIFICATION_DAYS = 365


def student_verification_expired(profile, now=None):
    """Return True after the student's verification expiry date has passed."""
    if not profile or not profile.user or profile.user.role != "STUDENT":
        return False
    if profile.verification_status != "VERIFIED" or not profile.verification_expires_at:
        return False
    current = now or datetime.now(timezone.utc)
    return current.date() > profile.verification_expires_at.date()


def borrower_eligibility(profile, now=None):
    if not profile:
        return "PROFILE_REQUIRED"
    if student_verification_expired(profile, now):
        return "REVIEW_REQUIRED"
    if profile.verification_status == "VERIFIED":
        return "ACTIVE"
    return profile.verification_status


def effective_verification_status(profile, now=None):
    return "REVIEW_REQUIRED" if student_verification_expired(profile, now) else (
        profile.verification_status if profile else "PENDING_VERIFICATION"
    )
