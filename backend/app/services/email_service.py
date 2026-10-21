import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def send_email(recipient, subject, body, sender_override=None):
    mail_server = current_app.config.get("MAIL_SERVER")
    sender = sender_override or current_app.config.get("MAIL_DEFAULT_SENDER")
    if not recipient or not mail_server or not sender:
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    port = current_app.config.get("MAIL_PORT", 587)
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    context = ssl.create_default_context()
    if current_app.config.get("MAIL_USE_SSL"):
        with smtplib.SMTP_SSL(mail_server, port, timeout=10, context=context) as server:
            if username:
                server.login(username, password or "")
            server.send_message(message)
        return True

    with smtplib.SMTP(mail_server, port, timeout=10) as server:
        if current_app.config.get("MAIL_USE_TLS", True):
            server.starttls(context=context)
        if username:
            server.login(username, password or "")
        server.send_message(message)
    return True


def send_account_approval_email(user):
    official_email = current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com")
    subject = "Your PCDS Library Account Has Been Approved"
    body = (
        f"Hello {user.full_name},\n\n"
        "Your PCDS Library account has been approved. You can now sign in and use the library system.\n\n"
        "PCDS Library"
    )
    return send_email(user.email, subject, body, sender_override=official_email)


def send_account_status_email(user, status):
    official_email = current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com")
    approved = status == "VERIFIED"
    subject = "Your PCDS Library Account Has Been Approved" if approved else "PCDS Library Account Registration Update"
    body = (
        f"Hello {user.full_name},\n\n"
        + ("Your PCDS Library account has been approved. You can now sign in and use the library system."
           if approved else "Your PCDS Library registration was not approved. Please contact the library for the next steps.")
        + "\n\nPCDS Library"
    )
    return send_email(user.email, subject, body, sender_override=official_email)


def send_library_account_alert(user):
    library_email = current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com")
    return send_email(
        library_email,
        "New PCDS Library Account Awaiting Approval",
        f"A new borrower account is awaiting review.\n\nName: {user.full_name}\nEmail: {user.email}\nRole: {user.role}\n\nOpen Desktop Admin > User Management to review the account.",
        sender_override=library_email,
    )


def send_borrow_request_email(item, event):
    subjects = {
        "submitted": "Your PCDS Library Borrow Request Was Submitted",
        "approved": "Your PCDS Library Borrow Request Was Approved",
        "rejected": "Your PCDS Library Borrow Request Was Rejected",
    }
    title = item.book.title if item.book else (item.requested_title or "Unknown book")
    details = {
        "submitted": "Your request is now waiting for library staff review.",
        "approved": "Your request was approved. Please review the due date in your PCDS Library account.",
        "rejected": "Your request was not approved. Contact the library if you need more information.",
    }
    body = f"Hello {item.user.full_name},\n\nBook: {title}\nStatus: {event.title()}\n{details[event]}\n\nPCDS Library"
    return send_email(item.user.email, subjects[event], body, sender_override=current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com"))


def send_return_email(loan, late_days, penalty_amount):
    body = (
        f"Hello {loan.user.full_name},\n\nYour book return has been recorded.\n\n"
        f"Book: {loan.book.title}\nReturned: {loan.returned_at.strftime('%B %d, %Y')}\n"
        f"Overdue days: {late_days}\nPenalty amount: PHP {penalty_amount:.2f}\n\nPCDS Library"
    )
    return send_email(loan.user.email, "Your PCDS Library Book Return Was Recorded", body, sender_override=current_app.config.get("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com"))


def send_penalty_emails(penalty, event):
    borrower = penalty.user
    loan = penalty.loan
    book_title = loan.book.title if loan and loan.book else "Unknown book"
    status_label = penalty.status.title()
    amount = f"PHP {penalty.amount:.2f}"
    event_label = "recorded" if event == "created" else "updated"
    subject = f"PCDS Library penalty {event_label}: {book_title}"

    borrower_body = (
        f"Hello {borrower.full_name},\n\n"
        f"A library penalty has been {event_label}.\n\n"
        f"Book: {book_title}\n"
        f"Overdue days: {penalty.late_days}\n"
        f"Penalty amount: {amount}\n"
        f"Payment status: {status_label}\n\n"
        "Please contact the PCDS Library if you have questions about this penalty."
    )
    library_body = (
        f"Penalty {event_label} in the PCDS Library system.\n\n"
        f"Borrower: {borrower.full_name}\n"
        f"Borrower email: {borrower.email or 'Not available'}\n"
        f"School ID: {borrower.school_id or 'Not available'}\n"
        f"Book: {book_title}\n"
        f"Overdue days: {penalty.late_days}\n"
        f"Penalty amount: {amount}\n"
        f"Payment status: {status_label}\n"
        f"Penalty ID: {penalty.penalty_id}\n"
    )

    delivered = []
    if borrower.email and send_email(borrower.email, subject, borrower_body):
        delivered.append(borrower.email)
    library_email = current_app.config.get("PENALTY_ALERT_EMAIL", "pcds.libraries@gmail.com")
    if library_email and library_email not in delivered and send_email(library_email, subject, library_body):
        delivered.append(library_email)
    return delivered
