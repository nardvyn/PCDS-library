import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "penalty-test-secret-key-at-least-32-bytes"

from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models.book import Book
from app.models.borrow_request import BorrowRequest
from app.models.borrower_profile import BorrowerProfile
from app.models.library_setting import LibrarySetting
from app.models.loan import Loan
from app.models.penalty import Penalty
from app.models.user import User


class PenaltyFlowTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, MAIL_SERVER="", MAIL_DEFAULT_SENDER="")
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

        self.admin = User(full_name="Library Admin", email="admin@test.local", role="ADMIN", account_status="ACTIVE")
        self.borrower = User(full_name="Test Borrower", email="borrower@test.local", role="STUDENT", account_status="ACTIVE")
        db.session.add_all([self.admin, self.borrower])
        db.session.flush()
        db.session.add(LibrarySetting(setting_key="daily_penalty", setting_value="10.00", updated_by=self.admin.user_id))
        db.session.commit()
        self.token = create_access_token(identity=str(self.admin.user_id), additional_claims={"role": "ADMIN"})
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def create_loan(self, due_days_from_now):
        suffix = str(abs(due_days_from_now))
        book = Book(title=f"Test Book {suffix}", author="Test Author", accession_number=f"TEST-{suffix}", total_copies=1, available_copies=0)
        db.session.add(book)
        db.session.flush()
        request = BorrowRequest(user_id=self.borrower.user_id, book_id=book.book_id, status="APPROVED")
        db.session.add(request)
        db.session.flush()
        now = datetime.now(timezone.utc)
        loan = Loan(request_id=request.request_id, user_id=self.borrower.user_id, book_id=book.book_id, borrowed_at=now - timedelta(days=10), due_date=now + timedelta(days=due_days_from_now), status="ACTIVE")
        db.session.add(loan)
        db.session.commit()
        return loan

    def test_overdue_return_creates_penalty_and_admin_totals(self):
        loan = self.create_loan(-3)
        with patch("app.routes.library_routes.send_penalty_emails") as send_penalty_emails:
            response = self.client.post(
                f"/api/library/loans/{loan.loan_id}/return",
                json={"condition": "GOOD"},
                headers={"Authorization": f"Bearer {self.token}"},
            )
            send_penalty_emails.assert_called_once()
            self.assertEqual(send_penalty_emails.call_args.args[1], "created")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["late_days"], 3)
        self.assertEqual(response.get_json()["penalty_amount"], 30.0)
        self.assertEqual(Penalty.query.filter_by(loan_id=loan.loan_id).one().amount, 30)

        penalties = self.client.get("/api/library/penalties", headers={"Authorization": f"Bearer {self.token}"})
        payload = penalties.get_json()
        self.assertEqual(penalties.status_code, 200)
        self.assertEqual(len(payload["penalties"]), 1)
        self.assertEqual(payload["total_penalties"], 30.0)
        self.assertEqual(payload["unpaid_penalties"], 30.0)
        self.assertEqual(payload["paid_penalties"], 0.0)

        penalty_id = payload["penalties"][0]["penalty_id"]
        with patch("app.routes.library_routes.send_penalty_emails") as send_penalty_emails:
            paid = self.client.patch(f"/api/library/penalties/{penalty_id}/pay", headers={"Authorization": f"Bearer {self.token}"})
            self.assertEqual(paid.status_code, 200)
            send_penalty_emails.assert_called_once()
            self.assertEqual(send_penalty_emails.call_args.args[1], "updated")

    def test_on_time_return_has_no_penalty(self):
        loan = self.create_loan(2)
        response = self.client.post(
            f"/api/library/loans/{loan.loan_id}/return",
            json={"condition": "GOOD"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["late_days"], 0)
        self.assertEqual(response.get_json()["penalty_amount"], 0)
        self.assertIsNone(Penalty.query.filter_by(loan_id=loan.loan_id).first())

    def test_active_overdue_loan_automatically_appears_in_penalties(self):
        loan = self.create_loan(-2)

        penalties = self.client.get("/api/library/penalties", headers={"Authorization": f"Bearer {self.token}"})

        self.assertEqual(penalties.status_code, 200)
        payload = penalties.get_json()
        self.assertEqual(len(payload["penalties"]), 1)
        self.assertEqual(payload["penalties"][0]["loan_id"], loan.loan_id)
        self.assertEqual(payload["penalties"][0]["late_days"], 2)
        self.assertEqual(payload["penalties"][0]["amount"], 20.0)
        self.assertEqual(payload["unpaid_penalties"], 20.0)

    def test_return_reuses_automatic_penalty_record(self):
        loan = self.create_loan(-2)
        self.client.get("/api/library/penalties", headers={"Authorization": f"Bearer {self.token}"})

        with patch("app.routes.library_routes.send_penalty_emails"):
            returned = self.client.post(
                f"/api/library/loans/{loan.loan_id}/return",
                json={"condition": "GOOD"},
                headers={"Authorization": f"Bearer {self.token}"},
            )

        self.assertEqual(returned.status_code, 200)
        self.assertEqual(Penalty.query.filter_by(loan_id=loan.loan_id).count(), 1)
        self.assertEqual(Penalty.query.filter_by(loan_id=loan.loan_id).one().amount, 20)

    def test_account_approval_sends_email_automatically(self):
        profile = BorrowerProfile(user_id=self.borrower.user_id, verification_status="PENDING_VERIFICATION")
        db.session.add(profile)
        db.session.commit()
        with patch("app.routes.verification_routes.borrower_profile_is_complete", return_value=True), patch("app.routes.verification_routes.send_account_approval_email", return_value=True) as send_email:
            approved = self.client.patch(
                f"/api/verification/profiles/{profile.profile_id}",
                json={"status": "VERIFIED"},
                headers={"Authorization": f"Bearer {self.token}"},
            )
            self.assertEqual(approved.status_code, 200)
            self.assertTrue(approved.get_json()["approval_email_sent"])
            self.assertIn("sent automatically", approved.get_json()["message"])
            send_email.assert_called_once()
            self.assertEqual(send_email.call_args.args[0].email, self.borrower.email)


if __name__ == "__main__":
    unittest.main()
