from datetime import datetime, timezone
from decimal import Decimal

from app.extensions import db
from app.models.library_setting import LibrarySetting
from app.models.loan import Loan
from app.models.penalty import Penalty


def sync_active_overdue_penalties(now=None):
    """Create or refresh penalties for every active loan past its due date."""
    now = now or datetime.now(timezone.utc)
    setting = db.session.get(LibrarySetting, "daily_penalty")
    daily_penalty = Decimal(setting.setting_value if setting else "10.00")
    changed = False
    overdue_loans = Loan.query.filter(Loan.status == "ACTIVE", Loan.due_date < now).all()

    for loan in overdue_loans:
        late_days = max((now.date() - loan.due_date.date()).days, 0)
        if late_days == 0:
            continue
        amount = Decimal(late_days) * daily_penalty
        penalty = Penalty.query.filter_by(loan_id=loan.loan_id).first()
        if penalty is None:
            db.session.add(Penalty(loan_id=loan.loan_id, user_id=loan.user_id, amount=amount, late_days=late_days, status="UNPAID"))
            changed = True
        elif penalty.late_days != late_days or penalty.amount != amount:
            penalty.late_days = late_days
            penalty.amount = amount
            if penalty.status == "PAID":
                penalty.status = "UNPAID"
                penalty.paid_at = None
            changed = True

    if changed:
        db.session.commit()
    return changed
