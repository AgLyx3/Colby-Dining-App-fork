from website import create_app, db
from website.models import Administrator
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys
import argparse


def add_admin(email, password):
    app = create_app()
    with app.app_context():
        try:
            # Create new admin
            new_admin = Administrator(
                admin_email=email,
                password_hashed=generate_password_hash(password),
                created_at=datetime.utcnow()
            )

            db.session.add(new_admin)
            db.session.commit()
            print(f"Successfully added administrator: {email}")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error adding administrator: {str(e)}")
            return False


def remove_admin(email):
    app = create_app()
    with app.app_context():
        try:
            # Find admin by email
            admin = Administrator.query.filter_by(admin_email=email).first()

            if not admin:
                print(f"No administrator found with email: {email}")
                return False

            # Remove the admin
            db.session.delete(admin)
            db.session.commit()

            print(f"Successfully removed administrator: {email}")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error removing administrator: {str(e)}")
            return False

def validate_email(email):
    """
    Validate that the email is a @colby.edu address
    """
    if not email.endswith('@colby.edu'):
        raise argparse.ArgumentTypeError("Email must be a @colby.edu address")
    return email



def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Manage administrator users")

    # Create mutually exclusive group to ensure only one action is performed
    group = parser.add_mutually_exclusive_group(required=True)

    # Add admin argument
    group.add_argument('--add', nargs=1, metavar=('EMAIL'),
                       type=str, help='Add a new admin (email password)')

    # Remove admin argument
    group.add_argument('--remove', type=validate_email,
                       help='Remove an existing admin (email)')

    # Parse arguments
    args = parser.parse_args()

    # Handle remove admin action
    if args.remove:
        confirmation = input(f"Are you sure you want to remove admin {args.remove}? (y/n): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled")
            sys.exit(0)

        # Attempt to remove admin, exit with appropriate status code
        result = remove_admin(args.remove)
        sys.exit(0 if result else 1)

    # Handle add admin action
    if args.add:
        email = args.add[0]

        # Validate email
        try:
            validate_email(email)
        except argparse.ArgumentTypeError as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Attempt to add admin, exit with appropriate status code
        result = add_admin(email, password='12345')  # hard-coded password
        sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()