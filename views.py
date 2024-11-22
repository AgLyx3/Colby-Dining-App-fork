
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask import Blueprint, render_template, redirect, url_for
from flask import request
from models import db, Food, Tag, food_tags
from flask_login import login_required, current_user
from utils import filter_foods, get_all_foods
from flask import Blueprint, render_template, jsonify
from flask import Blueprint, render_template, jsonify, request, redirect, session, url_for
from flask_login import current_user, login_required
from datetime import datetime
import os
import logging
from auth import admin_required
from dining_predictor import DiningHallPredictor
from models import db, FeedbackQuestion, Administrator, Response
from email_utils import EmailSender

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_blueprint = Blueprint('main', __name__)

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


