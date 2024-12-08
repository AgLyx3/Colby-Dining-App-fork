from app import create_app, db
from models import Administrator
import traceback

def update_database():
    app = create_app()
    with app.app_context():
        try:
            # Drop and recreate the Administrator table
            Administrator.__table__.drop(db.engine, checkfirst=True)
            db.create_all()
            print("Database structure updated successfully!")
            
            return True
        except Exception as e:
            print("Error updating database:", str(e))
            print("Traceback:")
            print(traceback.format_exc())
            return False

if __name__ == "__main__":
    update_database()