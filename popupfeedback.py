from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, FeedbackQuestion, YesNoResponse, RatingResponse, ShortAnswerResponse
import logging
import google.generativeai as genai

genai.configure(api_key="")
model = genai.GenerativeModel("gemini-1.5-flash")

# response = model.generate_content("Explain how AI works")
# print(response.text)



logging.basicConfig(level=logging.DEBUG)

popup_feedback_bp = Blueprint('popup_feedback', __name__)

@popup_feedback_bp.route('/submit-feedback', methods=['POST'])
def handle_popup_feedback():
    data = request.get_json()

    question_id = data.get('question_id')
    question_type = data.get('question_type')
    user_id = data.get('user_id')

    if not question_id or not question_type or not user_id:
        return jsonify({'error': 'Invalid data'}), 400

    question = FeedbackQuestion.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    if question.question_type != question_type:
        return jsonify({'error': 'Question type mismatch'}), 400

    if question_type == 'yes_no':
        response = YesNoResponse(
            feedback_id=question_id,
            user_id=user_id,
            content=str(data.get('is_yes')),
            is_yes=data.get('is_yes')
        )
    elif question_type == 'rating':
        response = RatingResponse(
            feedback_id=question_id,
            user_id=user_id,
            content=str(data.get('rating')),
            rating=data.get('rating')
        )
    elif question_type == 'short_answer':

        user_answer = data.get('answer_text')

        gemini_response = model.generate_content("This is a feedback response submitted by a user, if it is clearly not a valid feedback for dining service or is rude, output rude_or_irrelevant, else ouput the answer as it is, user answer: " + user_answer)

        response = ShortAnswerResponse(
            feedback_id=question_id,
            user_id=user_id,
            content=data.get('answer_text'),
            answer_text=gemini_response
        )
    else:
        return jsonify({'error': 'Unknown question type'}), 400

    db.session.add(response)
    db.session.commit()
    return jsonify({'message': 'Feedback submitted successfully'}), 200

@popup_feedback_bp.route('/check-for-popup', methods=['GET'])
def check_for_popup():
    """Finds all active feedback questions and triggers the one created the earliest."""
    logging.debug("Received request to check for popup.")
    current_date = datetime.utcnow()


    # active_questions = FeedbackQuestion.query.filter(
    #     FeedbackQuestion.active_start_date <= current_date,
    #     FeedbackQuestion.active_end_date >= current_date
    # ).order_by(FeedbackQuestion.created_at).all()
    #
    # if not active_questions:
    #     logging.debug("No active feedback questions found.")
    #     return jsonify({'message': 'No active feedback questions'}), 200

    # earliest_question = active_questions[0]

    earliest_question = FeedbackQuestion.query.offset(0).limit(1).first()

    logging.debug(f"Triggering popup for question ID {earliest_question.id}, Text: {earliest_question.question_text}")
    return jsonify({
        'message': 'Popup triggered',
        'question_id': earliest_question.id,
        'question_text': earliest_question.question_text,
        'question_type': earliest_question.question_type
    }), 200
