from app import create_app
from models import Administrator, db
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()
def add_admin(email, password):
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

if __name__ == "__main__":
    email = input("Enter admin email (@colby.edu): ")
    if not email.endswith('@colby.edu'):
        print("Error: Email must be a @colby.edu address")
        exit(1)
        
    password = input("Enter admin password: ")
    add_admin(email, password)