from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
menu_bp = Blueprint('menu', __name__)

def get_menu_service():
    """Get menu service instance with credentials"""
    from menu_api import BonAppetitAPI
    return BonAppetitAPI(
        username='colbycollege',  # Hardcoded for now
        password='G5YTx1652Xr2ZdaPST+a'  # Hardcoded for now
    )

@menu_bp.route('/current')
def get_menu():
    """Get menu for a specific dining hall and date"""
    try:
        dining_hall = request.args.get('dining_hall', 'Dana')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        logger.info(f"Fetching menu for {dining_hall} on {date}")
        
        menu_service = get_menu_service()
        hall_id = menu_service.DINING_HALLS.get(dining_hall)
        
        if not hall_id:
            logger.error(f"Invalid dining hall: {dining_hall}")
            return jsonify({
                'status': 'error',
                'error': 'Invalid dining hall',
                'menu': {}
            }), 200  # Return 200 even for invalid dining hall
            
        # Get raw menu data first
        raw_menu_data = menu_service.get_menu(hall_id, date)
        
        if not raw_menu_data or not raw_menu_data.get('days'):
            logger.error(f"No menu data available for {dining_hall} on {date}")
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