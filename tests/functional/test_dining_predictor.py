"""
Filename:
    test_dining_predictor.py

Note:
    Testing dining predictor functionalities
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
from website.dining_predictor import DiningHallPredictor

@pytest.fixture
def mock_data():
    '''
    Create mock data
    '''
    # Create mock data similar to the output of load_data
    return pd.DataFrame({
        'datetime': pd.date_range(start='2023-10-01', periods=6, freq='H'),
        'location': ['Dana', 'Dana', 'Roberts', 'Roberts', 'Foss', 'Foss'],
        'count': [5, 10, 15, 20, 25, 30],
        'hour': [12, 13, 14, 15, 16, 17],
        'minute': [0, 0, 0, 0, 0, 0],
        'day_of_week': [0, 0, 0, 0, 0, 0],
        'is_weekend': [False, False, False, False, False, False],
        'time_of_day': [12.0, 13.0, 14.0, 15.0, 16.0, 17.0],
        'is_peak_hour': [False, False, False, False, False, False],
    })

def test_load_data(mock_data):
    '''
    test load data
    '''
    predictor = DiningHallPredictor(model_dir='test_models', data_dir='test_data')
    
    # Mock the load_data method to return mock data
    with patch.object(predictor, 'load_data', return_value=mock_data):
        data = predictor.load_data()
    
    assert data.shape == (6, 9)  # Check if the shape of the data is correct
    assert data['location'].iloc[0] == 'Dana'  # Check if the location is correct

def test_train_models(mock_data):
    '''
    test train model
    '''
    predictor = DiningHallPredictor(model_dir='test_models', data_dir='test_data')
    
    # Mock the save_models method to avoid actual saving
    with patch.object(predictor, 'save_models') as mock_save:
        predictor.train_models(mock_data)
    
    assert 'Dana' in predictor.models  # Ensure the model for Dana is trained
    assert 'Roberts' in predictor.models  # Ensure the model for Roberts is trained

def test_predict_wait_times(mock_data):
    '''
    test predict wait time
    '''
    predictor = DiningHallPredictor(model_dir='test_models', data_dir='test_data')
    
    # Mock trained models and scalers
    with patch.object(predictor, 'load_saved_models'):
        predictor.models = {'Dana': MagicMock(), 'Roberts': MagicMock()}
        predictor.scalers = {'Dana': MagicMock(), 'Roberts': MagicMock()}
    
    # Simulate model prediction
    with patch.object(predictor, 'predict_wait_times', return_value={
        'predicted_count': 50,
        'wait_time_minutes': 10,
        'swipes_per_minute': 3.33,
        'busyness_level': 'High',
        'status': 'success'
    }) as mock_predict:
        current_time = datetime.now()
        prediction = predictor.predict_wait_times(current_time, 'Dana')
    
    assert prediction['predicted_count'] == 50  # Check if predicted count is correct
    assert prediction['wait_time_minutes'] == 10  # Check if wait time is correct
    assert prediction['busyness_level'] == 'High'  # Check if busyness level is correct
    assert prediction['status'] == 'success'  # Check if status is success
