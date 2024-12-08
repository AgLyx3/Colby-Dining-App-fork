from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


db = SQLAlchemy()

class Student(db.Model, UserMixin):
    student_email = db.Column(db.String(255), primary_key=True)
    student_access_token = db.Column(db.String(255), unique=True, nullable=False)
    fav = db.relationship('Favorites', backref='student')

    def get_id(self):
        return self.student_email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False
    
    
# Association table for the many-to-many relationship between Food and Tag
food_tags = db.Table('food_tags',
    db.Column('food_id', db.Integer, db.ForeignKey('food.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)  # e.g., 'Lunch', 'Vegetarian', 'Main Dining Hall'
    type = db.Column(db.String(50), nullable=False)  # e.g., 'Meal', 'Diet', 'Location'


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    label = db.Column(db.String(255))
    calories = db.Column(db.Integer)

    fav = db.relationship('Favorites', backref = 'food')

    # Many-to-many relationship with Tag
    tags = db.relationship('Tag', secondary=food_tags, backref='foods')



class Favorites(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created_at = db.Column(db.Date, nullable = False)
    update_at = db.Column(db.Date, nullable = False)
    student_email = db.Column(db.String(255), db.ForeignKey('student.student_email'), nullable = False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable = False)

class FavoriteDish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(255), db.ForeignKey('student.student_email'), nullable=False)
    dish_name = db.Column(db.String(255), nullable=False)  # We'll use dish name as unique identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('student_email', 'dish_name'),)

class Administrator(db.Model, UserMixin):
    admin_email = db.Column(db.String(255), primary_key=True)
    password_hashed = db.Column(db.String(128), nullable=False)
    google_id = db.Column(db.String(255), unique=True)  # For OAuth
    fullname = db.Column(db.String(255))  # From Google
    given_name = db.Column(db.String(255))  # From Google
    family_name = db.Column(db.String(255))  # From Google
    picture = db.Column(db.String(255))  # Google profile picture URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship with FeedbackQuestion
    feedback_questions = db.relationship(
        'FeedbackQuestion', 
        backref='administrator',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def get_id(self):
        """Required for Flask-Login"""
        return self.admin_email

    def __repr__(self):
        return f'<Administrator {self.admin_email}>'

class FeedbackQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    active_start_date = db.Column(db.Date, nullable=False)
    active_end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    administrator_id = db.Column(db.String(255), db.ForeignKey('administrator.admin_email'), nullable=False)

    # Relationship with Response (one-to-many)
    responses = db.relationship(
        'Response', 
        backref='feedback_question', 
        cascade='all, delete-orphan', 
        lazy='dynamic'
    )


class Response(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text, nullable = False)
    #feedback_id = db.Column(db.Integer, db.ForeignKey('feedback.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('feedback_question.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class WaitTime(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    location = db.Column(db.String(255), nullable = False)
    num_swipes = db.Column(db.Integer)
    start_time = db.Column(db.Time, nullable = False)
    end_time = db.Column(db.Time, nullable = False)
    date = db.Column(db.Date, nullable = False)
    day_of_week = db.Column(db.Integer, nullable = False)
    predicted_wait = db.Column(db.Integer, nullable = False)



