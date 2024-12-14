"""
Filename:
    menu_routes.py
"""
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)
menu_bp = Blueprint('menu', __name__)

def get_menu_service():
    """Get menu service instance with credentials"""
    from .menu_api import BonAppetitAPI
    username = os.getenv('MENU_API_USERNAME')
    password = os.getenv('MENU_API_PASSWORD')
    if not username or not password:
        raise ValueError("Menu API credentials not found in environment variables")
    return BonAppetitAPI(
        username= username,
password= password)

@menu_bp.route('/current')
def get_menu():
    """Get menu for a specific dining hall and date"""
    try:
        dining_hall = request.args.get('dining_hall', 'Dana')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        logger.info("Fetching menu for %s on %s", dining_hall, date)
        menu_service = get_menu_service()
        hall_id = menu_service.DINING_HALLS.get(dining_hall)
        if not hall_id:
            logger.error("Invalid dining hall: %s", dining_hall)
            return jsonify({
                'status': 'error',
                'error': 'Invalid dining hall',
                'menu': {}
            }), 200  # Return 200 even for invalid dining hall
        # Get raw menu data first
        raw_menu_data = menu_service.get_menu(hall_id, date)
        if not raw_menu_data or not raw_menu_data.get('days'):
            logger.error("No menu data available for %s on %s", dining_hall, date)
            return jsonify({
                'status': 'error',
                'error': 'No menu data available',
                'menu': {}
            }), 200  # Return 200 for no menu data
        # Process menu data
        processed_menu = menu_service.process_menu_data(raw_menu_data)
        if not processed_menu:
            logger.error("Failed to process menu data")
            return jsonify({
                'status': 'error',
                'error': 'Failed to process menu data',
                'menu': {}
            }), 200
# Get operating hours
        hours_data = {}
        try:
            hours_data = menu_service.get_cafe_hours(hall_id)
        except Exception as e:
            logger.warning(f"Failed to fetch hours: {str(e)}")
        return jsonify({
            'status': 'success',
            'dining_hall': dining_hall,
            'date': date,
            'hours': hours_data,
            'menu': processed_menu
        })
    except Exception as e:
        logger.error(f"Error in get_menu: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'menu': {}
        }), 200  # Always return 200 with error in data

@menu_bp.route('/debug/raw')
def get_raw_menu():
    """Debug endpoint to get raw menu data"""
    try:
        dining_hall = request.args.get('dining_hall', 'Dana')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        menu_service = get_menu_service()
        hall_id = menu_service.DINING_HALLS.get(dining_hall)
        if not hall_id:
            return jsonify({'error': 'Invalid dining hall'}), 200
        raw_data = menu_service.get_menu(hall_id, date)
        return jsonify(raw_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 200
