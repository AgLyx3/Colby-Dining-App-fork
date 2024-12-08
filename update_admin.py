from app import create_app, db
from models import Administrator
from werkzeug.security import generate_password_hash
from datetime import datetime

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

if __name__ == "__main__":
    email = input("Enter admin email to remove (@colby.edu): ")
    if not email.endswith('@colby.edu'):
        print("Error: Email must be a @colby.edu address")
        exit(1)
    confirmation = input(f"Are you sure you want to remove admin {email}? (y/n): ")
    if confirmation.lower() != 'y':
        print("Operation cancelled")
        exit(0)
        
    remove_admin(email)

    # email = input("Enter admin email (@colby.edu): ")
    # if not email.endswith('@colby.edu'):
    #     print("Error: Email must be a @colby.edu address")
    #     exit(1)
        
    # password = input("Enter admin password: ")
    # add_admin(email, password)

