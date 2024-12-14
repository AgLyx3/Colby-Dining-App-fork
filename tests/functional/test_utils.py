"""
Filename:
    test_utils.py

Note:
    Tests for general utility functions in utils.py
"""

import pytest
from website.utils import general_utils, create_tags, filter_foods, format_menu_items, get_popular_foods, get_food_counts_by_meal, get_food_counts_by_diet, get_all_foods, deactivate_expired_questions
from datetime import datetime


def test_make_food_info():
    """
    Test make_food_info structure creation.
    """
    food_info = general_utils.make_food_info(
        1, "Pasta", "Delicious Italian pasta", 500, ["Vegetarian", "Gluten Free"]
    )
    assert isinstance(food_info, dict)
    assert food_info["id"] == 1
    assert food_info["name"] == "Pasta"
    assert "Gluten Free" in food_info["tags"]


def test_format_date():
    """
    Test format_date for valid and invalid inputs.
    """
    date = datetime(2024, 12, 25)
    formatted_date = general_utils.format_date(date)
    assert formatted_date == "2024-12-25"

    formatted_date = general_utils.format_date("2024-12-25")
    assert formatted_date == "2024-12-25"


def test_calculate_percentage():
    """
    Test calculate_percentage function.
    """
    assert general_utils.calculate_percentage(50, 100) == 50.0
    assert general_utils.calculate_percentage(25, 200) == 12.5
    assert general_utils.calculate_percentage(0, 0) == 0


def test_is_valid_email():
    """
    Test is_valid_email function.
    """
    assert general_utils.is_valid_email("test@example.com") is True
    assert general_utils.is_valid_email("invalid-email") is False
    assert general_utils.is_valid_email("test@.com") is False


def test_sanitize_input():
    """
    Test sanitize_input function.
    """
    sanitized = general_utils.sanitize_input("  Hello World  ")
    assert sanitized == "hello world"
    sanitized = general_utils.sanitize_input(12345)
    assert sanitized == "12345"


def test_calculate_average():
    """
    Test calculate_average function.
    """
    assert general_utils.calculate_average([10, 20, 30]) == 20
    assert general_utils.calculate_average([]) == 0
    assert general_utils.calculate_average([100]) == 100

def test_create_menu_struct():
    """
    Test create_menu_struct creates a valid structure.
    """
    menu = general_utils.create_menu_struct(
        "Breakfast Menu", "Morning specials", []
    )
    assert isinstance(menu, dict)
    assert menu["name"] == "Breakfast Menu"
    assert menu["description"] == "Morning specials"
    assert menu["items"] == []


def test_edit_menu_name():
    """
    Test edit_menu_name modifies the name attribute.
    """
    menu = {"name": "Old Menu", "description": "Test", "items": []}
    updated_menu = general_utils.edit_menu_name(menu, "New Menu")
    assert updated_menu["name"] == "New Menu"


def test_edit_menu_description():
    """
    Test edit_menu_description modifies the description attribute.
    """
    menu = {"name": "Menu", "description": "Old Description", "items": []}
    updated_menu = general_utils.edit_menu_description(menu, "New Description")
    assert updated_menu["description"] == "New Description"


def test_add_item_to_menu():
    """
    Test add_item_to_menu adds an item to the menu.
    """
    menu = {"name": "Menu", "description": "Test", "items": []}
    item = {"id": 1, "name": "Pancakes", "description": "Fluffy pancakes"}
    updated_menu = general_utils.add_item_to_menu(menu, item)
    assert len(updated_menu["items"]) == 1
    assert updated_menu["items"][0]["name"] == "Pancakes"


def test_remove_item_from_menu():
    """
    Test remove_item_from_menu removes an item by its ID.
    """
    menu = {
        "name": "Menu",
        "description": "Test",
        "items": [{"id": 1, "name": "Pancakes"}],
    }
    updated_menu = general_utils.remove_item_from_menu(menu, 1)
    assert len(updated_menu["items"]) == 0


def test_clear_menu_items():
    """
    Test clear_menu_items clears all items from the menu.
    """
    menu = {
        "name": "Menu",
        "description": "Test",
        "items": [{"id": 1, "name": "Pancakes"}],
    }
    updated_menu = general_utils.clear_menu_items(menu)
    assert updated_menu["items"] == []

def test_create_tag_struct():
    """Test create_tag_struct function."""
    tag = general_utils.create_tag_struct("Vegan", "FoodType")
    assert tag["name"] == "Vegan"
    assert tag["type"] == "FoodType"


def test_update_tag_name():
    """Test update_tag_name function."""
    tag = {"name": "Breakfast", "type": "Meal"}
    updated_tag = general_utils.update_tag_name(tag, "Lunch")
    assert updated_tag["name"] == "Lunch"


def test_update_tag_type():
    """Test update_tag_type function."""
    tag = {"name": "Breakfast", "type": "Meal"}
    updated_tag = general_utils.update_tag_type(tag, "FoodType")
    assert updated_tag["type"] == "FoodType"


def test_add_food_to_menu():
    """Test add_food_to_menu function."""
    menu = {"name": "Menu", "description": "Test", "items": []}
    food = {"id": 1, "name": "Pasta", "description": "Delicious pasta"}
    updated_menu = general_utils.add_food_to_menu(menu, food)
    assert len(updated_menu["items"]) == 1
    assert updated_menu["items"][0]["name"] == "Pasta"


def test_count_items_in_menu():
    """Test count_items_in_menu function."""
    menu = {
        "name": "Menu",
        "description": "Test",
        "items": [{"id": 1, "name": "Pasta"}],
    }
    count = general_utils.count_items_in_menu(menu)
    assert count == 1


def test_create_feedback_question():
    """Test create_feedback_question function."""
    question = general_utils.create_feedback_question(
        "Is the food fresh?", "2024-01-01", "2024-12-31", True
    )
    assert question["question_text"] == "Is the food fresh?"
    assert question["is_active"] is True


def test_deactivate_question():
    """Test deactivate_question function."""
    question = {
        "question_text": "Is the food fresh?",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "is_active": True,
    }
    updated_question = general_utils.deactivate_question(question)
    assert updated_question["is_active"] is False


def test_is_question_active():
    """Test is_question_active function."""
    question = {
        "question_text": "Is the food fresh?",
        "is_active": True,
    }
    assert general_utils.is_question_active(question) is True
    question["is_active"] = False
    assert general_utils.is_question_active(question) is False


def test_merge_menus():
    """Test merge_menus function."""
    menu1 = {"name": "Menu1", "description": "Test1", "items": []}
    menu2 = {"name": "Menu2", "description": "Test2", "items": [{"id": 2, "name": "Burger"}]}
    merged_menu = general_utils.merge_menus(menu1, menu2)
    assert len(merged_menu["items"]) == 1
    assert merged_menu["items"][0]["name"] == "Burger"


def test_duplicate_menu():
    """Test duplicate_menu function."""
    menu = {"name": "Menu", "description": "Test", "items": [{"id": 1, "name": "Pasta"}]}
    duplicated_menu = general_utils.duplicate_menu(menu)
    assert duplicated_menu is not menu  # Ensure it's a new object
    assert duplicated_menu["items"][0] == menu["items"][0]
    duplicated_menu["items"].append({"id": 2, "name": "Burger"})
    assert len(menu["items"]) == 1  # Original menu should not be affected


def test_create_menu_struct():
    """Test create_menu_struct function."""
    menu = general_utils.create_menu_struct("Dinner Menu", "Served from 6 PM to 9 PM")
    assert menu["name"] == "Dinner Menu"
    assert menu["description"] == "Served from 6 PM to 9 PM"
    assert menu["items"] == []


def test_add_tag_to_food():
    """Test add_tag_to_food function."""
    food = {"name": "Salad", "tags": []}
    updated_food = general_utils.add_tag_to_food(food, "Vegan")
    assert "Vegan" in updated_food["tags"]


def test_remove_tag_from_food():
    """Test remove_tag_from_food function."""
    food = {"name": "Salad", "tags": ["Vegan"]}
    updated_food = general_utils.remove_tag_from_food(food, "Vegan")
    assert "Vegan" not in updated_food["tags"]


def test_update_menu_description():
    """Test update_menu_description function."""
    menu = {"name": "Lunch Menu", "description": "Old description"}
    updated_menu = general_utils.update_menu_description(menu, "New description")
    assert updated_menu["description"] == "New description"


def test_find_food_by_name():
    """Test find_food_by_name function."""
    menu = {
        "name": "Dinner Menu",
        "items": [{"name": "Pizza"}, {"name": "Burger"}],
    }
    food = general_utils.find_food_by_name(menu, "Pizza")
    assert food["name"] == "Pizza"


def test_update_food_calories():
    """Test update_food_calories function."""
    food = {"name": "Burger", "calories": 500}
    updated_food = general_utils.update_food_calories(food, 600)
    assert updated_food["calories"] == 600


def test_deactivate_all_questions():
    """Test deactivate_all_questions function."""
    questions = [{"is_active": True}, {"is_active": True}]
    updated_questions = general_utils.deactivate_all_questions(questions)
    assert all(not q["is_active"] for q in updated_questions)


def test_calculate_total_calories():
    """Test calculate_total_calories function."""
    menu = {
        "items": [
            {"name": "Pizza", "calories": 300},
            {"name": "Burger", "calories": 500},
        ]
    }
    total_calories = general_utils.calculate_total_calories(menu)
    assert total_calories == 800


def test_get_tag_count():
    """Test get_tag_count function."""
    tags = ["Vegan", "Gluten Free", "Organic"]
    count = general_utils.get_tag_count(tags)
    assert count == 3


def test_create_feedback_struct():
    """Test create_feedback_struct function."""
    feedback = general_utils.create_feedback_struct(
        "Is the service good?", "2024-01-01", "2024-12-31", True
    )
    assert feedback["question_text"] == "Is the service good?"
    assert feedback["is_active"] is True
    assert feedback["start_date"] == "2024-01-01"
    assert feedback["end_date"] == "2024-12-31"
