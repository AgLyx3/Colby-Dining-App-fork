"""
Filename:
    utils.py
"""
from datetime import datetime
from website import db
from .models import Tag, Food, FeedbackQuestion


def create_tags():
    """create tags"""
    if Tag.query.count() == 0:  # Check if tags already exist
        tags = [
            Tag(name="Dana", type="Location"),
            Tag(name="Roberts", type="Location"),
            Tag(name="Foss", type="Location"),
            Tag(name="Breakfast", type="Meal"),
            Tag(name="Lunch", type="Meal"),
            Tag(name="Dinner", type="Meal"),
            Tag(name="Vegan", type="FoodType"),
            Tag(name="Vegetarian", type="FoodType"),
            Tag(name="Gluten Free", type="FoodType"),
            Tag(name="Farm to Fork", type="FoodType"),
            Tag(name="Humane", type="FoodType"),
            Tag(name="Organic", type="FoodType")
        ]

        db.session.bulk_save_objects(tags)
        db.session.commit()


def filter_foods(selected_tags):
    """filter foods"""
    # Step 1: Retrieve tags matching the selected tags
    selected_tag_names = selected_tags  # Assume these are passed in from the query string or form
    tags = Tag.query.filter(Tag.name.in_(selected_tag_names)).all()

    # Step 2: Query food items that have the selected tags
    filtered_foods = Food.query.join(Food.tags).filter(Tag.id.in_([tag.id for tag in tags])).all()

    return format_menu_items(filtered_foods)


def format_menu_items(foods):
    """format menu items"""
    formatted_items = []

    for food in foods:
        item = {
            "id": food.id,
            "name": food.name,
            "description": food.description,
            "calories": food.calories,
            "tags": [tag.name for tag in food.tags]
        }
        formatted_items.append(item)

    return formatted_items


def get_popular_foods(limit=5):
    """get popular foods"""
    # Query the most popular foods based on the number of favorites
    popular_foods = Food.query.join(Food.fav).group_by(Food.id).order_by(db.func.count(Food.id).desc()).limit(
        limit).all()

    return format_menu_items(popular_foods)


def get_food_counts_by_meal():
    """get food counts by meal"""
    # Query the count of food items for each meal type
    meal_counts = db.session.query(Tag.name, db.func.count(Food.id)).join(Food.tags).filter(
        Tag.type == 'Meal').group_by(Tag.name).all()

    return dict(meal_counts)


def get_food_counts_by_diet():
    """get food counts by diet"""
    # Query the count of food items for each diet type
    diet_counts = db.session.query(Tag.name, db.func.count(Food.id)).join(Food.tags).filter(
        Tag.type == 'FoodType').group_by(Tag.name).all()
    return dict(diet_counts)


def get_all_foods():
    """
    Fetch all the food items from the database.
    """
    foods = Food.query.all()
    return format_menu_items(foods)


def deactivate_expired_questions():
    """deactivate expired questions"""
    today = datetime.today().date()
    expired_questions = FeedbackQuestion.query.filter(
        FeedbackQuestion.active_end_date < today,
        FeedbackQuestion.is_active is True
    ).all()
    if not expired_questions:
        print("No expired questions to deactivate.")
        return

    for question in expired_questions:
        question.is_active = False
    try:
        db.session.commit()
        print(f'{len(expired_questions)} questions deactivated due to expired end date.')
    except Exception as e:
        db.session.rollback()
        print(f"Error deactivating questions: {e}")

class GeneralUtils:
    """
    A collection of general utility functions.
    """

    @staticmethod
    def make_food_info(id, name, description, calories, tags):
        """
        Create a structured dictionary for food info.
        """
        return {
            "id": id,
            "name": name,
            "description": description,
            "calories": calories,
            "tags": tags,
        }

    @staticmethod
    def format_date(date):
        """
        Format a date into a human-readable string.
        """
        return date.strftime("%Y-%m-%d") if isinstance(date, datetime) else str(date)

    @staticmethod
    def calculate_percentage(part, whole):
        """
        Calculate percentage from part and whole.
        """
        if whole == 0:
            return 0
        return round((part / whole) * 100, 2)

    @staticmethod
    def is_valid_email(email):
        """
        Validate if the given string is an email.
        """
        import re
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def sanitize_input(value):
        """
        Sanitize input by stripping leading/trailing spaces and converting to lowercase.
        """
        return str(value).strip().lower()

    @staticmethod
    def calculate_average(numbers):
        """
        Calculate the average of a list of numbers.
        """
        return sum(numbers) / len(numbers) if numbers else 0

    @staticmethod
    def create_menu_struct(name, description, items):
        """
        Create a structured dictionary for a menu.
        """
        return {
            "name": name,
            "description": description,
            "items": items,  # List of food item structures
        }

    @staticmethod
    def edit_menu_name(menu, new_name):
        """
        Edit the name attribute of a menu structure.
        """
        menu["name"] = new_name
        return menu

    @staticmethod
    def edit_menu_description(menu, new_description):
        """
        Edit the description attribute of a menu structure.
        """
        menu["description"] = new_description
        return menu

    @staticmethod
    def add_item_to_menu(menu, item):
        """
        Add an item to the items list of a menu structure.
        """
        menu["items"].append(item)
        return menu

    @staticmethod
    def remove_item_from_menu(menu, item_id):
        """
        Remove an item from the items list of a menu structure by its ID.
        """
        menu["items"] = [item for item in menu["items"] if item.get("id") != item_id]
        return menu

    @staticmethod
    def clear_menu_items(menu):
        """
        Clear all items from a menu structure.
        """
        menu["items"] = []
        return menu

    @staticmethod
    def create_tag_struct(name, type_):
        """Create a structured dictionary for a tag."""
        return {"name": name, "type": type_}

    @staticmethod
    def update_tag_name(tag, new_name):
        """Update the name of a tag structure."""
        tag["name"] = new_name
        return tag

    @staticmethod
    def update_tag_type(tag, new_type):
        """Update the type of a tag structure."""
        tag["type"] = new_type
        return tag

    @staticmethod
    def add_food_to_menu(menu, food):
        """Add a food structure to the items list of a menu."""
        menu["items"].append(food)
        return menu

    @staticmethod
    def count_items_in_menu(menu):
        """Count the number of items in the menu."""
        return len(menu["items"])

    @staticmethod
    def create_feedback_question(question_text, start_date, end_date, is_active):
        """Create a structured dictionary for a feedback question."""
        return {
            "question_text": question_text,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": is_active,
        }

    @staticmethod
    def deactivate_question(question):
        """Deactivate a feedback question."""
        question["is_active"] = False
        return question

    @staticmethod
    def is_question_active(question):
        """Check if a feedback question is active."""
        return question["is_active"]

    @staticmethod
    def merge_menus(menu1, menu2):
        """Merge two menus by combining their items."""
        menu1["items"].extend(menu2["items"])
        return menu1

    @staticmethod
    def duplicate_menu(menu):
        """Create a deep copy of a menu structure."""
        import copy
        return copy.deepcopy(menu)

    @staticmethod
    def create_menu_struct(name, description):
        """Create a structured dictionary for a menu."""
        return {"name": name, "description": description, "items": []}

    @staticmethod
    def add_tag_to_food(food, tag_name):
        """Add a tag name to a food's tags list."""
        food["tags"].append(tag_name)
        return food

    @staticmethod
    def remove_tag_from_food(food, tag_name):
        """Remove a tag name from a food's tags list if it exists."""
        if tag_name in food["tags"]:
            food["tags"].remove(tag_name)
        return food

    @staticmethod
    def update_menu_description(menu, new_description):
        """Update the description of a menu."""
        menu["description"] = new_description
        return menu

    @staticmethod
    def find_food_by_name(menu, food_name):
        """Find a food item in a menu by its name."""
        for item in menu["items"]:
            if item["name"] == food_name:
                return item
        return None

    @staticmethod
    def update_food_calories(food, new_calories):
        """Update the calories of a food item."""
        food["calories"] = new_calories
        return food

    @staticmethod
    def deactivate_all_questions(questions):
        """Deactivate all feedback questions."""
        for question in questions:
            question["is_active"] = False
        return questions

    @staticmethod
    def calculate_total_calories(menu):
        """Calculate the total calories of all food items in a menu."""
        return sum(food.get("calories", 0) for food in menu["items"])

    @staticmethod
    def get_tag_count(tags):
        """Count the number of tags in the list."""
        return len(tags)

    @staticmethod
    def create_feedback_struct(question_text, start_date, end_date, is_active):
        """Create a feedback structure."""
        return {
            "question_text": question_text,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": is_active,
        }


# Instantiate an object for utility functions
general_utils = GeneralUtils()
