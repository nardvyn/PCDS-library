import argparse
from getpass import getpass

from sqlalchemy import func

from app import create_app
from app.extensions import db
from app.models.user import User


VALID_ROLES = {"ADMIN", "LIBRARIAN"}


def main():
    parser = argparse.ArgumentParser(description="Create a PCDS Library desktop staff account.")
    parser.add_argument("--school-id", help="Unique staff ID used at desktop login")
    parser.add_argument("--email", help="Email used at desktop login")
    parser.add_argument("--name", help="Staff full name")
    parser.add_argument("--role", choices=sorted(VALID_ROLES), help="Desktop access role")
    parser.add_argument("--reset-password", action="store_true", help="Update the password of an existing staff account")
    args = parser.parse_args()

    if args.reset_password and not (args.school_id or args.email):
        parser.error("Provide --school-id or --email to identify the existing account.")
    if not args.reset_password and not all((args.school_id, args.email, args.name, args.role)):
        parser.error("--school-id, --email, --name, and --role are required when creating an account.")

    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 8:
        parser.error("Password must contain at least 8 characters.")
    if password != confirmation:
        parser.error("Passwords do not match.")

    app = create_app()
    with app.app_context():
        if args.reset_password:
            staff_by_id = (
                User.query.filter(func.lower(User.school_id) == args.school_id.strip().lower()).first()
                if args.school_id
                else None
            )
            staff_by_email = (
                User.query.filter_by(email=args.email.strip().lower()).first()
                if args.email
                else None
            )
            if staff_by_id and staff_by_email and staff_by_id.user_id != staff_by_email.user_id:
                parser.error("The supplied staff ID and email belong to different accounts.")
            existing_staff = staff_by_id or staff_by_email
            if not existing_staff:
                parser.error("No existing staff account matched. No account was created.")
            if existing_staff.role not in VALID_ROLES:
                parser.error("Only ADMIN and LIBRARIAN accounts can be updated by this command.")
            existing_staff.set_password(password)
            db.session.commit()
            print(f"Updated password for existing {existing_staff.role} account.")
            return

        existing_staff = User.query.filter(func.lower(User.school_id) == args.school_id.strip().lower()).first()
        if existing_staff:
            parser.error("That school ID already exists. Use --reset-password to change its password.")

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
