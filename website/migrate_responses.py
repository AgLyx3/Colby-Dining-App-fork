"""
Filename:
    migrate_responses.py
"""
from website import create_app, db
from .models import Response
from sqlalchemy import text

def update_responses_table():
    app = create_app()
    with app.app_context():
        try:
            # Add student_email column using modern SQLAlchemy syntax
            with db.engine.connect() as conn:
                conn.execute(text(
                '''
                    ALTER TABLE response 
                    ADD COLUMN student_email VARCHAR(255) REFERENCES student(student_email)
                '''))
                conn.commit()
            
            print("Successfully added student_email column to Response table")
            
        except Exception as e:
            print(f"Error updating Response table: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    update_responses_table()