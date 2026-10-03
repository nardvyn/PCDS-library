import argparse
from getpass import getpass

from app import create_app
from app.extensions import db
from app.models.user import User


VALID_ROLES = {"ADMIN", "LIBRARIAN"}


def main():
    parser = argparse.ArgumentParser(description="Create a PCDS Library desktop staff account.")
    parser.add_argument("--school-id", required=True, help="Unique staff ID used at desktop login")
    parser.add_argument("--email", required=True, help="Email used at desktop login")
    parser.add_argument("--name", required=True, help="Staff full name")
    parser.add_argument("--role", required=True, choices=sorted(VALID_ROLES), help="Desktop access role")
    parser.add_argument("--reset-password", action="store_true", help="Update the password of an existing staff account")
    args = parser.parse_args()

    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 8:
        parser.error("Password must contain at least 8 characters.")
    if password != confirmation:
        parser.error("Passwords do not match.")

    app = create_app()
    with app.app_context():
        existing_staff = User.query.filter_by(school_id=args.school_id).first()
        if existing_staff and not args.reset_password:
            parser.error("That school ID already exists. Use --reset-password to change its password.")

        if existing_staff:
            if existing_staff.role not in VALID_ROLES:
                parser.error("Only ADMIN and LIBRARIAN accounts can be updated by this command.")
            existing_staff.full_name = args.name
            existing_staff.email = args.email.strip().lower()
            existing_staff.role = args.role
            existing_staff.account_status = "ACTIVE"
            existing_staff.set_password(password)
            db.session.commit()
            print(f"Updated password for {args.role} account {args.school_id}.")
            return

        staff = User(
            school_id=args.school_id,
            full_name=args.name,
            email=args.email.strip().lower(),
            role=args.role,
            account_status="ACTIVE",
        )
        staff.set_password(password)
        db.session.add(staff)
        db.session.commit()
        print(f"Created {args.role} account for {args.school_id}.")


if __name__ == "__main__":
    main()
