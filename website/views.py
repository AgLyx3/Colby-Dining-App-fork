"""
Filename: views.py
"""
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask import Blueprint, render_template, redirect, url_for
from flask import request, current_app
# from models import db, Food, Tag, food_tags
from flask_login import login_required, current_user
from website.utils import filter_foods, get_all_foods
from flask import Blueprint, render_template, jsonify
from flask import Blueprint, render_template, jsonify, request, redirect, session, url_for
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import os
import logging
from website.auth import admin_required
from website.dining_predictor import DiningHallPredictor
from website.models import db, FeedbackQuestion, Administrator
from website.email_utils import EmailSender
from typing import Dict, List, Optional
from website.menu_api import BonAppetitAPI

# from website import db
from website.models import Student, Food, Tag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_blueprint = Blueprint('main', __name__)
menu_bp = Blueprint('menu', __name__)

email_sender = EmailSender()

# Initialize predictor
base_dir = os.path.dirname(os.path.abspath(__file__))
predictor = None
predictor_initialized = False

def initialize_predictor():
    """Initialize the DiningHallPredictor with models"""
    global predictor, predictor_initialized
    try:
        predictor = DiningHallPredictor(
            model_dir=os.path.join(base_dir, 'ml_models'),
            data_dir=os.path.join(base_dir, 'data')
        )
        
        if not any(predictor.models):
            logger.info("No saved models found, training new models...")
            df = predictor.load_data('October-*.csv')
            predictor.train_models(df, save=True)
        
        predictor_initialized = True
        logger.info("Predictor initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize predictor: {str(e)}")
        return False

# Initialize predictor when blueprint is created
initialize_predictor()

@main_blueprint.context_processor
def inject_user():
    """Make current_user available to all templates"""
    return dict(current_user=current_user)

# Basic routes
@main_blueprint.route('/')
def index():
    """
    Routing to home page 
    """

    # Rendering the template
    return render_template('index.html')


@main_blueprint.route('/dining-experience')
def dining_experience():
    """
    Routing to dining experience page 
    """
    return render_template('dining_experience.html')

@main_blueprint.route('/team')
def team():
    """
    Routing to team page 
    """
    return render_template('team.html')


@main_blueprint.route('/menu', methods=['GET'])
def menu():
    """
    Routing to menu page
    """
    # Get the selected tags from the query parameters
    selected_tags = request.args.getlist('tags')  # List of tags selected by the user

    # If no tags are selected, return all foods
    if not selected_tags:
        filtered_foods = get_all_foods()  # Fetch all food items
    else:
        filtered_foods = filter_foods(selected_tags)  # Filter foods based on selected tags

    # Get all available tags for the filter bar
    all_tags = Tag.query.all()

    # Pass the filtered food items and selected tags to the template
    return render_template('menu.html', foods=filtered_foods, selected_tags=selected_tags, all_tags=all_tags)



@main_blueprint.route('/contact')
def contact():
    """
    Routing to the contact page 
    """
    return render_template('contact.html')

# Dashboard routes
@main_blueprint.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    Routing to admin dashboard
    """
    return render_template('admindashboard.html')

@main_blueprint.route('/userdashboard')
@login_required
def userdashboard():
    """
    Routing to the user dashboard
    """
    if isinstance(current_user, Administrator):
        return redirect(url_for('main.admin_dashboard'))
    return render_template('userdashboard.html')

# Feedback question routes
@main_blueprint.route('/admin/feedback-question', methods=['POST'])
@login_required
@admin_required
def create_feedback_question():
    """
    Method for admin to create feedback question on the admin dashboard
    """
    try:
        new_question = FeedbackQuestion(
            question_text=request.form.get('questionText'),
            question_type=request.form.get('questionType'),
            active_start_date=datetime.strptime(request.form.get('activeStartDate'), '%Y-%m-%d').date(),
            active_end_date=datetime.strptime(request.form.get('activeEndDate'), '%Y-%m-%d').date(),
            administrator_id=current_user.admin_email
        )
        db.session.add(new_question)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Question created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@main_blueprint.route('/admin/feedback-question/<int:question_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_feedback_question(question_id):
    """
    Method for removing question from the front-end 
    (controversial: we don't actually want to delete the question from the database)
    """
    try:
        question = FeedbackQuestion.query.get_or_404(question_id)
        if question.administrator_id != current_user.admin_email:
            return jsonify({'status': 'error', 'message': 'Unauthorized to delete this question'}), 403
        
        db.session.delete(question)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Question deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@main_blueprint.route('/api/admin/feedback-questions', methods=['GET'])
def get_feedback_questions():
    """
    Method for getting feedback questions
    """
    try:
        questions = FeedbackQuestion.query.order_by(FeedbackQuestion.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'questions': [{
                'id': q.id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'active_start_date': q.active_start_date.isoformat(),
                'active_end_date': q.active_end_date.isoformat(),
                'created_at': q.created_at.isoformat() if q.created_at else None
            } for q in questions]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Wait times API
@main_blueprint.route('/api/wait-times')
def get_wait_times():
    """Get wait time predictions for dining halls"""
    try:
        if not predictor_initialized:
            logger.error("Predictor not properly initialized")
            raise Exception("Prediction service unavailable")

        current_time = datetime.now()
        predictions = {}
        
        for location in ['Dana', 'Roberts', 'Foss']:
            try:
                prediction = predictor.predict_wait_times(current_time, location)
                if prediction:
                    predictions[location] = {
                        'status': 'closed' if prediction.get('status') == 'closed' else 'success',
                        'message': prediction.get('message', None),
                        'crowd': prediction.get('predicted_count', None),
                        'wait_time': prediction.get('wait_time_minutes', None)
                    }
                else:
                    predictions[location] = {
                        'status': 'error',
                        'message': 'No prediction available'
                    }
            except Exception as e:
                logger.error(f"Error predicting for {location}: {str(e)}")
                predictions[location] = {
                    'status': 'error',
                    'message': 'Temporarily unavailable'
                }
        
        return jsonify({
            'status': 'success',
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'predictions': predictions
        })
        
    except Exception as e:
        logger.error(f"Error in wait-times endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Service temporarily unavailable',
            'predictions': {location: {'status': 'error', 'message': 'Temporarily unavailable'} 
                          for location in ['Dana', 'Roberts', 'Foss']}
        }), 500
    
@main_blueprint.route('/userdashboard')
@login_required
def user_dashboard():
    """
    Routing to the dashboard based on the user roles: 
    student -> user dashboard;
    admin -> admin dashboard.
    """
    if isinstance(current_user, Administrator):
        return redirect(url_for('main.admin_dashboard'))
    return render_template('userdashboard.html')

@main_blueprint.route('/logout', methods=['POST'])
def logout():
    """
    Log out 
    """
    session.clear()
    return redirect(url_for('main.index'))

@main_blueprint.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    Method for submitting feedback
    """
    try:
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        feedback_type = request.form.get('feedback_type')
        message = request.form.get('message')
        
        # Validate required fields
        if not all([name, email, feedback_type, message]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields.'
            }), 400
            
        # Use the instance method
        success = email_sender.send_feedback_email(
            name=name,
            email=email,
            feedback_type=feedback_type,
            message=message
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Thank you for your feedback! We will get back to you soon.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'There was an error sending your feedback. Please try again later.'
            }), 500
            
    except Exception as e:
        print(f"Error processing feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@main_blueprint.route('/menu')
def menu_page():  
    """
    Routing to menu page and filters
    """
    today = datetime.now()
    return render_template('menu.html', 
        locations=["Dana", "Roberts", "Foss"],
        dietary_filters=[
            {"id": "vegetarian", "label": "Vegetarian", "value": "vegetarian"},
            {"id": "vegan", "label": "Vegan", "value": "vegan"},
            {"id": "gluten-free", "label": "Gluten Free", "value": "gluten-free"},
            {"id": "halal", "label": "Halal", "value": "halal"},
        ],
        today_date=today.strftime('%Y-%m-%d'),
        min_date=today.strftime('%Y-%m-%d'),
        max_date=(today + timedelta(days=7)).strftime('%Y-%m-%d')
    )


@menu_bp.route('/api/menu/current', methods=['GET'])
def get_current_menus():
    """
    API: getting current menus
    """
    try:
        # Get menu service instance 
        menu_service = BonAppetitAPI(
            username=current_app.config['MENU_API_USERNAME'],
            password=current_app.config['MENU_API_PASSWORD']
        )

        date = datetime.now().strftime('%Y-%m-%d')
        menus = menu_service.get_all_dining_hall_menus(date)

        return jsonify({
            'status': 'success',
            'date': date,
            'menus': menus
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
@menu_bp.route('/<dining_hall>')
def get_dining_hall_menu(dining_hall):
    """
    API: getting menus by dining hall
    """
    try:
        menu_service = BonAppetitAPI(
            username=current_app.config['MENU_API_USERNAME'],
            password=current_app.config['MENU_API_PASSWORD']
        )
        
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        logger.info(f"Fetching menu for {dining_hall} on {date}")
        
        # Get correct cafe ID
        cafe_id = menu_service.DINING_HALLS.get(dining_hall)
        if not cafe_id:
            return jsonify({'status': 'error', 'message': 'Invalid dining hall'}), 400
            
        menu_data = menu_service.get_menu(cafe_id, date)
        if menu_data:
            processed_menu = menu_service.process_menu_data(menu_data)
            return jsonify({
                'status': 'success',
                'menu': processed_menu
            })
        
        return jsonify({
            'status': 'error', 
            'message': 'No menu data available'
        }), 404
        
    except Exception as e:
        logger.error(f"Error fetching menu: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@menu_bp.route('/api/menu/weekly/<dining_hall>', methods=['GET'])
def get_weekly_menu(dining_hall: str):
    """Get weekly menu for a specific dining hall"""
    try:
        # Validate dining hall
        dining_hall = dining_hall.title()
        if dining_hall not in current_app.menu_service.DINING_HALLS:
            return jsonify({
                'status': 'error',
                'message': 'Invalid dining hall'
            }), 400
            
        # Calculate date range
        today = datetime.now().date()
        dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') 
                for i in range(7)]
                
        weekly_menu = {}
        cafe_id = current_app.menu_service.DINING_HALLS[dining_hall]
        
        for date in dates:
            # Try cache first
            cached_menu = current_app.menu_cache.get_cached_menu(date, dining_hall)
            if cached_menu:
                weekly_menu[date] = cached_menu
                continue
                
            # Fetch fresh data if needed
            menu_data = current_app.menu_service.get_menu(cafe_id, date)
            if menu_data:
                processed_menu = current_app.menu_service.process_menu_data(menu_data)
                weekly_menu[date] = processed_menu
                current_app.menu_cache.save_menu_to_cache(date, dining_hall, processed_menu)
            else:
                weekly_menu[date] = []
                
        return jsonify({
            'status': 'success',
            'dining_hall': dining_hall,
            'weekly_menu': weekly_menu
        })
        
    except Exception as e:
        logger.error(f"Error fetching weekly menu for {dining_hall}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to fetch weekly menu'
        }), 500

@menu_bp.route('/api/menu/hours', methods=['GET'])
def get_dining_hours():
    """Get current operating hours for all dining halls"""
    try:
        menu_service = current_app.menu_service
        all_hours = {}
        
        for hall_name, hall_id in menu_service.DINING_HALLS.items():
            cafe_info = menu_service.get_cafe_info(hall_id)
            if cafe_info and 'cafes' in cafe_info:
                cafe_data = cafe_info['cafes'].get(hall_id, {})
                
                # Extract hours from dayparts
                today = datetime.now().date()
                today_str = today.strftime('%Y-%m-%d')
                
                hours = []
                for day in cafe_data.get('days', []):
                    if day.get('date') == today_str:
                        for daypart in day.get('dayparts', []):
                            hours.append({
                                'meal': daypart.get('label', ''),
                                'start_time': daypart.get('starttime', ''),
                                'end_time': daypart.get('endtime', ''),
                                'message': daypart.get('message', '')
                            })
                
                all_hours[hall_name] = {
                    'status': day.get('status', 'unknown'),
                    'message': day.get('message', ''),
                    'hours': hours
                }
            
        return jsonify({
            'status': 'success',
            'hours': all_hours
        })
        
    except Exception as e:
        logger.error(f"Error fetching dining hours: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to fetch dining hours'
        }), 500


