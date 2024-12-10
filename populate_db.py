from app import create_app
from models import db, WaitTime, Food, Tag, FeedbackQuestion, Response
from datetime import datetime, time, timedelta
import random

app = create_app()
def generate_wait_times():
    locations = ['Dana', 'Roberts', 'Foss']
    meal_times = [
        (time(7, 0), time(10, 0)),   # Breakfast
        (time(11, 0), time(14, 0)),  # Lunch  
        (time(17, 0), time(20, 0))   # Dinner
    ]

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    delta = end_date - start_date
    
    for day in range(delta.days + 1):
        current_date = start_date + timedelta(days=day)
        day_of_week = current_date.weekday()

        for location in locations:
            for start, end in meal_times:
                num_swipes = random.randint(50, 500)
                predicted_wait = random.randint(2, 25)
                
                wait_time = WaitTime(
                    location=location,
                    num_swipes=num_swipes,
                    start_time=start,
                    end_time=end,
                    date=current_date,
                    day_of_week=day_of_week,
                    predicted_wait=predicted_wait
                )
                db.session.add(wait_time)
    
    db.session.commit()
    print(f"Generated {WaitTime.query.count()} wait time records.")

def generate_foods_and_tags():
    # Create tags
    meal_tags = ['Breakfast', 'Brunch', 'Lunch', 'Dinner', 'Dessert', 'Late Night']
    diet_tags = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Contains Nuts', 'Dairy-Free', 'Halal', 'Kosher', 'Low Carb', 'High Protein', 'Organic']
    location_tags = ['Dana', 'Roberts', 'Foss']

    for name in meal_tags:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, type='Meal')
            db.session.add(tag)

    for name in diet_tags:  
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, type='Diet')
            db.session.add(tag)

    for name in location_tags:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, type='Location')  
            db.session.add(tag)

    db.session.commit()

    # Create foods
    foods = [
        {'name': 'Scrambled Eggs', 'description': 'Fluffy scrambled eggs', 'calories': 200, 
         'tags': ['Breakfast', 'Vegetarian', 'Gluten-Free', 'Dana', 'Roberts']},
        {'name': 'Pancakes', 'description': 'Buttermilk pancakes with syrup', 'calories': 350,
         'tags': ['Breakfast', 'Vegetarian', 'Dana', 'Roberts', 'Foss']},
        {'name': 'Bacon', 'description': 'Crispy bacon strips', 'calories': 250,
         'tags': ['Breakfast', 'Dana', 'Roberts', 'Foss']},
        {'name': 'Oatmeal', 'description': 'Creamy oatmeal with toppings', 'calories': 300,
         'tags': ['Breakfast', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Dana', 'Roberts']},
        {'name': 'Yogurt Parfait', 'description': 'Yogurt layered with granola and fruit', 'calories': 280,
         'tags': ['Breakfast', 'Vegetarian', 'Dana', 'Roberts', 'Foss-Grab n Go']},
        {'name': 'Breakfast Burrito', 'description': 'Tortilla with scrambled eggs, cheese, and salsa', 'calories': 450,
         'tags': ['Breakfast', 'Vegetarian', 'Dana', 'Roberts', 'Dana-Grab n Go']},
        {'name': 'Avocado Toast', 'description': 'Toasted bread topped with mashed avocado', 'calories': 320,
         'tags': ['Breakfast', 'Brunch', 'Vegetarian', 'Vegan', 'Dana', 'Roberts']},
        {'name': 'Eggs Benedict', 'description': 'Poached eggs on English muffin with hollandaise sauce', 'calories': 550,
         'tags': ['Brunch', 'Dana', 'Roberts']},
        {'name': 'Chicken Caesar Salad', 'description': 'Romaine lettuce with grilled chicken and Caesar dressing', 'calories': 400,
         'tags': ['Lunch', 'Gluten-Free', 'High Protein', 'Dana', 'Roberts', 'Foss']},
        {'name': 'Margherita Pizza', 'description': 'Pizza with tomato sauce, mozzarella, and basil', 'calories': 600,
         'tags': ['Lunch', 'Dinner', 'Vegetarian', 'Dana', 'Roberts', 'Foss']},
        {'name': 'Spaghetti Bolognese', 'description': 'Spaghetti with meat sauce', 'calories': 550,
         'tags': ['Lunch', 'Dinner', 'Dana', 'Roberts']},
        {'name': 'Veggie Burger', 'description': 'Plant-based patty on a bun with toppings', 'calories': 400,
         'tags': ['Lunch', 'Dinner', 'Vegetarian', 'Vegan', 'Dana', 'Roberts', 'Foss']},
        {'name': 'Grilled Salmon', 'description': 'Grilled salmon fillet with lemon and herbs', 'calories': 450,
         'tags': ['Lunch', 'Dinner', 'Gluten-Free', 'Dairy-Free', 'High Protein', 'Dana', 'Roberts']},
        {'name': 'Stir Fry', 'description': 'Stir-fried vegetables with tofu or chicken', 'calories': 380,
         'tags': ['Lunch', 'Dinner', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Dana', 'Roberts', 'Foss']},
        {'name': 'Chocolate Chip Cookies', 'description': 'Freshly baked chocolate chip cookies', 'calories': 120,
         'tags': ['Dessert', 'Vegetarian', 'Contains Nuts', 'Dana', 'Roberts', 'Foss', 'Dana-Grab n Go', 'Foss-Grab n Go']},
        {'name': 'Fruit Salad', 'description': 'Mixed seasonal fruits', 'calories': 80,
         'tags': ['Dessert', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Dana', 'Roberts', 'Foss', 'Dana-Grab n Go', 'Foss-Grab n Go']},
        {'name': 'Ice Cream', 'description': 'Assorted flavors of ice cream', 'calories': 200,
         'tags': ['Dessert', 'Vegetarian', 'Gluten-Free', 'Dana', 'Roberts']},
        {'name': 'Cheese Pizza', 'description': 'Pizza with tomato sauce and mozzarella cheese', 'calories': 550,
         'tags': ['Late Night', 'Vegetarian', 'Dana', 'Roberts']},
        {'name': 'Chicken Tenders', 'description': 'Breaded and fried chicken tenders', 'calories': 480,
         'tags': ['Late Night', 'Dana', 'Roberts']},
        {'name': 'French Fries', 'description': 'Crispy fried potato fries', 'calories': 300,
         'tags': ['Late Night', 'Vegetarian', 'Vegan', 'Gluten-Free', 'Dana', 'Roberts']}
    ]

    for food_data in foods:
        food = Food(
            name=food_data['name'], 
            description=food_data['description'],
            calories=food_data['calories']
        )
        
        for tag_name in food_data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                food.tags.append(tag)

        db.session.add(food)

    db.session.commit()  
    print(f"Generated {len(foods)} food records with tags.")

def generate_feedback():
    questions_data = [
        {
            "question_text": "Was the service helpful?",
            "question_type": "yes-no",
            "active_start_date": datetime(2024, 1, 1),
            "active_end_date": datetime(2024, 12, 31),
            "is_active": True,  # Active
            "administrator_id": "yli25@colby.edu",
            "responses": ["Yes", "No", "Yes"]
        },
        {
            "question_text": "Rate your satisfaction (1-5).",
            "question_type": "rating",
            "active_start_date": datetime(2024, 6, 1),
            "active_end_date": datetime(2024, 12, 31),
            "is_active": True,  # Active
            "administrator_id": "yli25@colby.edu",
            "responses": ["5", "4", "3", "5", "4"]
        },
        {
            "question_text": "Any additional feedback?",
            "question_type": "text",
            "active_start_date": datetime(2024, 1, 1),
            "active_end_date": datetime(2024, 3, 31),
            "is_active": False,  # Inactive
            "administrator_id": "yli25@colby.edu",
            "responses": [
                "The staff was very friendly.",
                "Please improve the timing of the service.",
                "Loved the ambiance!"
            ]
        }
    ]

    # Populate the database
    for question_data in questions_data:
        # Create question
        question = FeedbackQuestion(
            question_text=question_data["question_text"],
            question_type=question_data["question_type"],
            active_start_date=question_data["active_start_date"],
            active_end_date=question_data["active_end_date"],
            is_active=question_data["is_active"],  # Set is_active
            administrator_id=question_data["administrator_id"],
        )
        db.session.add(question)
        db.session.commit()  # Commit to generate the question ID

        # Add responses for the question
        for response_text in question_data["responses"]:
            response = Response(content=response_text, question_id=question.id)
            db.session.add(response)

    # Commit all responses
    db.session.commit()

    print("Feedback populated successfully!")


with app.app_context():
    db.drop_all
    db.create_all()
    # generate_wait_times() 
    # generate_foods_and_tags()
    generate_feedback()