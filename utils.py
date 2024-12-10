from models import db, Tag, Food, FeedbackQuestion
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from datetime import datetime

def create_tags():
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
    # Step 1: Retrieve tags matching the selected tags
    selected_tag_names = selected_tags  # Assume these are passed in from the query string or form
    tags = Tag.query.filter(Tag.name.in_(selected_tag_names)).all()
    
    # Step 2: Query food items that have the selected tags
    filtered_foods = Food.query.join(Food.tags).filter(Tag.id.in_([tag.id for tag in tags])).all()
    
    return format_menu_items(filtered_foods)

def get_all_foods():
    # Step 1: Query all food items from the Food table
    all_foods = Food.query.all()
    
    return format_menu_items(all_foods)

def format_menu_items(foods):
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
    # Query the most popular foods based on the number of favorites
    popular_foods = Food.query.join(Food.fav).group_by(Food.id).order_by(db.func.count(Food.id).desc()).limit(limit).all()
    
    return format_menu_items(popular_foods)

def get_food_counts_by_meal():
    # Query the count of food items for each meal type
    meal_counts = db.session.query(Tag.name, db.func.count(Food.id)).join(Food.tags).filter(Tag.type == 'Meal').group_by(Tag.name).all()
    
    return dict(meal_counts)

def get_food_counts_by_diet():
    # Query the count of food items for each diet type
    diet_counts = db.session.query(Tag.name, db.func.count(Food.id)).join(Food.tags).filter(Tag.type == 'FoodType').group_by(Tag.name).all()
    
    return dict(diet_counts)

def get_all_foods():
    """
    Fetch all the food items from the database.
    """
    foods = Food.query.all()
    return format_menu_items(foods)

def deactivate_expired_questions():
    today = datetime.today().date()
    
    expired_questions = FeedbackQuestion.query.filter(
        FeedbackQuestion.active_end_date < today, 
        FeedbackQuestion.is_active == True
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


