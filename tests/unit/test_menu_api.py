"""
Filename:
    test_menu_api

Note:
    Testing menu api
"""
from website.menu_api import *


def test_BonAppetitAPI():
    """
    Testing menu api object
    """
    menu_api = BonAppetitAPI(username="username", password="password")

    assert menu_api.username == "username"
    assert menu_api.password == "password"


def test_sort_meal_periods():
    """
    Testing menu sorting functionality
    """
    menu_api = BonAppetitAPI(username="username", password="password")
    menu_data = {
        "4": ["Dish 1", "Dish 2"],
        "1": ["Dish 3"],
        "3": ["Dish 4"],
        "2": ["Dish 5", "Dish 6"]
    }
    ordered_menu = menu_api._sort_meal_periods(menu_data)
    assert ordered_menu != None
    assert b'ordered_menu isinstance(OrderedDict)'


def test_process_menu_data():
    """
    Testing menu functionality
    """
    menu_api = BonAppetitAPI(username="username", password="password")
    menu_data = {
        "4": ["Dish 1", "Dish 2"],
        "1": ["Dish 3"],
        "3": ["Dish 4"],
        "2": ["Dish 5", "Dish 6"]
    }
    organized_menu = menu_api.process_menu_data(menu_data)

    assert organized_menu is not None


def test_get_menu():
    """
    Testing menu functionality
    """
    menu_api = BonAppetitAPI(username="username", password="password")
    menu = menu_api.get_menu("1447")
    assert menu is not None


def test_get_cafe_hours():
    """
    Testing menu functionality
    """
    menu_api = BonAppetitAPI(username="username", password="password")
    op_hours = menu_api.get_cafe_hours("1447")
    assert op_hours is not None
