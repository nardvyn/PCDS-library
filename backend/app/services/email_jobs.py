from datetime import datetime, timedelta, timezone
from decimal import Decimal

from flask import current_app

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.borrow_request import BorrowRequest
from app.models.library_setting import LibrarySetting
from app.models.loan import Loan
from app.models.penalty import Penalty
from app.services.audit_service import record_audit
from app.services.email_service import send_email


def already_sent_today(action, entity_id):
    today = datetime.now(timezone.utc).date()
    return AuditLog.query.filter_by(action=action, entity_id=str(entity_id)).filter(AuditLog.created_at >= datetime.combine(today, datetime.min.time())).first() is not None


def run_daily_email_notifications():
    setting = db.session.get(LibrarySetting, "notifications_enabled")
    if setting and setting.setting_value.lower() != "true":
        return {"disabled": True, "sent": 0}

    now = datetime.now(timezone.utc)
    daily_penalty = Decimal((db.session.get(LibrarySetting, "daily_penalty") or type("Setting", (), {"setting_value": "10.00"})()).setting_value)
    sent = 0
    for loan in Loan.query.filter_by(status="ACTIVE").all():
        days_until_due = (loan.due_date.date() - now.date()).days
        if days_until_due not in {3, 0} and days_until_due >= 0:
            continue
        action = "EMAIL_DUE_REMINDER_SENT" if days_until_due >= 0 else "EMAIL_OVERDUE_NOTICE_SENT"
        if already_sent_today(action, loan.loan_id) or not loan.user.email:
            continue
        late_days = max(-days_until_due, 0)
        amount = Decimal(late_days) * daily_penalty
        subject = "PCDS Library Book Due Reminder" if days_until_due >= 0 else "PCDS Library Overdue Book Notice"
        timing = "due today" if days_until_due == 0 else "due in 3 days" if days_until_due == 3 else f"overdue by {late_days} day(s)"
        body = f"Hello {loan.user.full_name},\n\nBook: {loan.book.title}\nStatus: {timing}\nDue date: {loan.due_date.strftime('%B %d, %Y')}\nCurrent penalty: PHP {amount:.2f}\n\nPCDS Library"
        try:
            if send_email(loan.user.email, subject, body, sender_override=current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com")):
                record_audit(None, action, "LOAN", loan.loan_id, f"Sent {subject} to {loan.user.email}.")
                sent += 1
        except Exception as error:
            current_app.logger.exception("Daily loan email failed for loan %s.", loan.loan_id)
            record_audit(None, "EMAIL_DELIVERY_FAILED", "LOAN", loan.loan_id, str(error))

    summary_key = now.date().isoformat()
    if not already_sent_today("EMAIL_DAILY_SUMMARY_SENT", summary_key):
        start = datetime.combine(now.date(), datetime.min.time())
        pending = BorrowRequest.query.filter_by(status="PENDING").count()
        new_penalties = Penalty.query.filter(Penalty.created_at >= start).all()
        total = sum((item.amount for item in new_penalties), Decimal("0"))
        body = f"PCDS Library daily summary for {now.date():%B %d, %Y}\n\nPending borrow requests: {pending}\nNew penalties: {len(new_penalties)}\nNew penalty total: PHP {total:.2f}\n"
        try:
            if send_email(current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com"), "PCDS Library Daily Requests and Penalties Summary", body, sender_override=current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com")):
                record_audit(None, "EMAIL_DAILY_SUMMARY_SENT", "DATE", summary_key, "Daily requests and penalties summary sent.")
                sent += 1
        except Exception as error:
            current_app.logger.exception("Daily library summary email failed.")
            record_audit(None, "EMAIL_DELIVERY_FAILED", "DATE", summary_key, str(error))
    db.session.commit()
    return {"disabled": False, "sent": sent}
