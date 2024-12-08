
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask import Blueprint, render_template, redirect, url_for
from flask import request, current_app
from models import db, Food, Tag, food_tags, Response
from flask_login import login_required, current_user
from utils import filter_foods, get_all_foods
from flask import Blueprint, render_template, jsonify
from flask import Blueprint, render_template, jsonify, request, redirect, session, url_for
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import os
import logging
from auth import admin_required
from dining_predictor import DiningHallPredictor
from models import db, FeedbackQuestion, Administrator, FavoriteDish
from email_utils import EmailSender
from typing import Dict, List, Optional
from menu_api import BonAppetitAPI

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

    # Rendering the template
    return render_template('index.html')


@main_blueprint.route('/dining-experience')
def dining_experience():
    return render_template('dining_experience.html')

@main_blueprint.route('/team')
def team():
    return render_template('team.html')




@main_blueprint.route('/menu', methods=['GET'])
def menu():
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
    return render_template('contact.html')

# Dashboard routes
@main_blueprint.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admindashboard.html')

@main_blueprint.route('/userdashboard')
@login_required
def userdashboard():
    if isinstance(current_user, Administrator):
        return redirect(url_for('main.admin_dashboard'))
    return render_template('userdashboard.html')

# Feedback question routes
@main_blueprint.route('/admin/feedback-question', methods=['POST'])
@login_required
@admin_required
def create_feedback_question():
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
    
@main_blueprint.route('/admin/feedback-question/get-response/<int:question_id>', methods=['GET'])
@login_required
@admin_required
def get_responses(question_id):
    question_type = request.args.get('question_type')
    
    # Fetch the question and responses from the database
    feedback_question = FeedbackQuestion.query.get(question_id)
    
    if not feedback_question:
        return jsonify({'error': 'Question not found'}), 404

    # Check if the question type matches the one in the query parameters
    if feedback_question.question_type != question_type:
        return jsonify({'error': 'Mismatched question type'}), 400

    # Get the responses
    responses = Response.query.filter_by(question_id=question_id).all()
    
    # Prepare the responses data based on the question type
    response_data = {'question': feedback_question.question_text, 'responses': {}}
    
    if question_type == 'yes-no':
        yes_count = 0
        no_count = 0
        for response in responses:
            if response.content.lower() == 'yes':
                yes_count += 1
            elif response.content.lower() == 'no':
                no_count += 1
        response_data['responses'] = {'yes': yes_count, 'no': no_count}
    
    elif question_type == 'rating':
        rating_counts = {str(i): 0 for i in range(1, 6)}  # Ratings 1 to 5
        for response in responses:
            if response.content in rating_counts:
                rating_counts[response.content] += 1
        response_data['responses'] = rating_counts
    
    elif question_type == 'text':
        text_responses = [response.content for response in responses]
        response_data['responses'] = text_responses
    
    # Return the responses as JSON
    return jsonify(response_data)

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
    if isinstance(current_user, Administrator):
        return redirect(url_for('main.admin_dashboard'))
    return render_template('userdashboard.html')

@main_blueprint.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main_blueprint.route('/submit_feedback', methods=['POST'])
def submit_feedback():
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
    

@main_blueprint.route('/api/favorites', methods=['POST', 'DELETE'])
@login_required
def manage_favorites():
    try:
        data = request.get_json()
        dish_name = data.get('dish_name')
        
        if not dish_name:
            return jsonify({'status': 'error', 'message': 'Dish name required'}), 400
            
        if request.method == 'POST':
            favorite = FavoriteDish(
                student_email=current_user.student_email,
                dish_name=dish_name
            )
            db.session.add(favorite)
            message = 'Dish added to favorites'
        else:  # DELETE
            favorite = FavoriteDish.query.filter_by(
                student_email=current_user.student_email,
                dish_name=dish_name
            ).first()
            
            if not favorite:
                return jsonify({'status': 'error', 'message': 'Favorite not found'}), 404
                
            db.session.delete(favorite)
            message = 'Dish removed from favorites'
            
        db.session.commit()
        return jsonify({'status': 'success', 'message': message})
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Dish already in favorites'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_blueprint.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites():
    try:
        favorites = FavoriteDish.query.filter_by(
            student_email=current_user.student_email
        ).order_by(FavoriteDish.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'favorites': [{'dish_name': f.dish_name} for f in favorites]
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


