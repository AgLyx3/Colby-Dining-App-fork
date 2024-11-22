import requests
from datetime import datetime
import logging
import base64
from typing import Dict, List, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

class BonAppetitAPI:
    """Service class to interact with Bon Appetit API"""
    
    BASE_URL = "https://cafemanager-api.cafebonappetit.com/api/2"
    DINING_HALLS = {
        "Dana": "1445",
        "Foss": "1446",
        "Roberts": "1447"
    }

    # Define meal period order
    MEAL_PERIOD_ORDER = [
        "Breakfast",
        "Lunch",
        "Lunch Lite",
        "Dinner",
        "Dinner Lite",
    ]

    def __init__(self, username: str, password: str):
        """Initialize with API credentials"""
        self.username = username
        self.password = password
        self.session = requests.Session()
        auth_str = f"{username}:{password}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'User-Agent': 'Colby-Dining/1.0',
            'Accept': 'application/json'
        })

    def _sort_meal_periods(self, menu_data: Dict[str, List[Dict]]) -> OrderedDict:
        """Sort meal periods in the correct order"""
        ordered_menu = OrderedDict()
        
        # First add meals in our defined order
        for meal_period in self.MEAL_PERIOD_ORDER:
            if meal_period in menu_data:
                ordered_menu[meal_period] = menu_data[meal_period]
        
        # Add any additional meal periods that weren't in our predefined order
        for meal_period in menu_data:
            if meal_period not in ordered_menu:
                ordered_menu[meal_period] = menu_data[meal_period]
                
        return ordered_menu

    def process_menu_data(self, menu_data: dict) -> Dict[str, List[Dict]]:
        """Process raw menu data into a simplified format grouped by meal period"""
        try:
            organized_menu = {}
            
            if not menu_data or 'days' not in menu_data or not menu_data['days']:
                logger.warning("No valid menu data to process")
                return organized_menu

            # Get the first day's data
            day = menu_data['days'][0]
            cafe_id = next(iter(day.get('cafes', {}).keys()))
            cafe_data = day['cafes'].get(cafe_id, {})

            # Get the icons/dietary information
            cor_icons = menu_data.get('cor_icons', {})
            
            # Process each daypart
            for daypart_list in cafe_data.get('dayparts', []):
                # Handle both list and dict daypart formats
                if isinstance(daypart_list, dict):
                    dayparts = [daypart_list]
                else:
                    dayparts = daypart_list

                for daypart in dayparts:
                    meal_period = daypart.get('label', '')
                    if not meal_period:
                        continue

                    organized_menu[meal_period] = []

                    # Process each station
                    for station in daypart.get('stations', []):
                        station_name = station.get('label', '')
                        items = station.get('items', [])

                        for item_id in items:
                            item_data = menu_data.get('items', {}).get(str(item_id))
                            if item_data:
                                # Process dietary flags
                                dietary_flags = []
                                cor_icon_ids = item_data.get('cor_icon', {})
                                for icon_id in cor_icon_ids:
                                    icon_info = cor_icons.get(icon_id, {})
                                    if icon_info.get('label'):
                                        dietary_flags.append(icon_info['label'])

                                menu_item = {
                                    'name': item_data.get('label', ''),
                                    'description': item_data.get('description', ''),
                                    'station': station_name,
                                    'dietary_flags': dietary_flags,
                                    'nutrition': {
                                        'calories': item_data.get('nutrition', {}).get('kcal', '')
                                    }
                                }
                                organized_menu[meal_period].append(menu_item)

            # Remove empty meal periods
            organized_menu = {k: v for k, v in organized_menu.items() if v}
            
            # Sort meal periods
            organized_menu = self._sort_meal_periods(organized_menu)
            
            logger.info(f"Successfully processed menu with {len(organized_menu)} meal periods")
            return organized_menu

        except Exception as e:
            logger.error(f"Error processing menu: {str(e)}")
            logger.error(f"Menu data causing error: {str(menu_data)[:200]}...")
            return {}

    def get_menu(self, cafe_id: str, date: Optional[str] = None) -> dict:
        """Fetch menu for a specific cafe and date"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
                
            url = f"{self.BASE_URL}/menus"
            params = {
                'cafe': cafe_id,
                'date': date
            }
            
            logger.info(f"Making request to {url} with params: {params}")
            auth = (self.username, self.password)
            response = self.session.get(url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received data structure: {str(data)[:200]}...")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching menu: {str(e)}")
            return {}

    def get_cafe_hours(self, cafe_id: str) -> dict:
        """Fetch cafe operating hours"""
        try:
            url = f"{self.BASE_URL}/cafes"
            params = {'cafe': cafe_id}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cafe_data = data.get('cafes', {}).get(cafe_id, {})
            
            today = datetime.now().strftime('%Y-%m-%d')
            operating_hours = {
                'status': 'unknown',
                'message': '',
                'dayparts': []
            }
            
            for day in cafe_data.get('days', []):
                if day.get('date') == today:
                    operating_hours['status'] = day.get('status', 'unknown')
                    operating_hours['message'] = day.get('message', '')
                    
                    for daypart_list in day.get('dayparts', []):
                        if isinstance(daypart_list, dict):
                            dayparts = [daypart_list]
                        else:
                            dayparts = daypart_list
                            
                        for dp in dayparts:
                            operating_hours['dayparts'].append({
                                'label': dp.get('label', ''),
                                'starttime': dp.get('starttime', ''),
                                'endtime': dp.get('endtime', ''),
                                'message': dp.get('message', '')
                            })
            
            return operating_hours
            
        except Exception as e:
            logger.error(f"Error fetching cafe hours: {str(e)}")
            return {
                'status': 'error',
                'message': 'Unable to fetch operating hours',
                'dayparts': []
            }