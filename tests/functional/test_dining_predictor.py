import pytest
from unittest.mock import MagicMock
import pandas as pd
from datetime import datetime
from website.dining_predictor import DiningHallPredictor


@pytest.fixture
def mock_dining_predictor(mocker):
    """
    Fixture to mock the DiningHallPredictor class and its methods.
    """
    # Mock the load_data method to return a sample DataFrame
    mock_load_data = mocker.patch('website.dining_predictor.DiningHallPredictor.load_data')
    mock_load_data.return_value = pd.DataFrame({
        'datetime': pd.to_datetime(['2024-12-14 08:00', '2024-12-14 12:00', '2024-12-14 18:00']),
        'location': ['Dana', 'Roberts', 'Foss'],
        'count': [100, 200, 150]
    })

    # Mock the train_models method to do nothing
    mock_train_models = mocker.patch('website.dining_predictor.DiningHallPredictor.train_models')
    mock_train_models.return_value = None

    # Mock the joblib load method to return a dummy model and scaler
    mock_load = mocker.patch('website.dining_predictor.joblib.load')
    mock_load.return_value = MagicMock()

    # Mock the joblib dump method to do nothing
    mock_dump = mocker.patch('website.dining_predictor.joblib.dump')
    mock_dump.return_value = None

    # Mock the load_saved_models method to populate models and scalers
    mock_load_saved_models = mocker.patch('website.dining_predictor.DiningHallPredictor.load_saved_models')
    mock_load_saved_models.return_value = None

    # Initialize the predictor
    predictor = DiningHallPredictor(model_dir='ml_models', data_dir='data')
    predictor.models = {'Dana': MagicMock(), 'Roberts': MagicMock(), 'Foss': MagicMock()}  # mock models
    predictor.scalers = {'Dana': MagicMock(), 'Roberts': MagicMock(), 'Foss': MagicMock()}  # mock scalers
    
    return predictor, mock_load_data, mock_train_models, mock_load, mock_dump, mock_load_saved_models

def test_predict_wait_times(mocker, mock_dining_predictor):
    """
    Test the predict_wait_times function.
    """
    predictor, _, _, _, _, _ = mock_dining_predictor

    # Mock the result of predict_wait_times
    mocker.patch.object(predictor, 'predict_wait_times', return_value={
        'predicted_count': 120,
        'wait_time_minutes': 10,
        'swipes_per_minute': 0.8,
        'busyness_level': 'Medium',
        'status': 'success'
    })
    
    current_time = datetime(2024, 12, 14, 12, 0)  # Mock current time to 12:00 PM
    prediction = predictor.predict_wait_times(current_time, 'Dana')

    # Assertions for the return value of predict_wait_times
    assert prediction['predicted_count'] == 120
    assert prediction['wait_time_minutes'] == 10
    assert prediction['swipes_per_minute'] == 0.8
    assert prediction['busyness_level'] == 'Medium'
    assert prediction['status'] == 'success'


def test_save_models(mock_dining_predictor):
    """
    Test saving models and scalers.
    """
    predictor, _, _, _, mock_dump, _ = mock_dining_predictor
    predictor.save_models()

    # Ensure that joblib.dump is called for each dining hall model and scaler
    for hall in predictor.dining_halls:
        # Check if dump was called for both model and scaler
        mock_dump.assert_any_call(f"ml_models/{hall.lower()}_model.joblib", predictor.models[hall])
        mock_dump.assert_any_call(f"ml_models/{hall.lower()}_scaler.joblib", predictor.scalers[hall])


def test_save_models(mock_dining_predictor):
    """
    Test saving models and scalers.
    """
    predictor, _, _, _, mock_dump, _ = mock_dining_predictor
    predictor.save_models()

    # Ensure that joblib.dump is called for each dining hall model and scaler
    for hall in predictor.dining_halls:
        mock_dump.assert_any_call(f"ml_models/{hall.lower()}_model.joblib", predictor.models[hall])
        mock_dump.assert_any_call(f"ml_models/{hall.lower()}_scaler.joblib", predictor.scalers[hall])


def test_prepare_features(mock_dining_predictor):
    """
    Test if the feature preparation function works as expected.
    """
    predictor, _, _, _, _, _ = mock_dining_predictor

    # Sample data frame to pass into prepare_features
    data = pd.DataFrame({
        'count': [100, 150, 200],
        'hour': [8, 12, 18],
        'minute': [0, 30, 0],
        'day_of_week': [0, 1, 2],
        'is_weekend': [False, False, False],
        'time_of_day': [8, 12.5, 18],
        'is_peak_hour': [True, True, True]
    })
    
    features = predictor.prepare_features(data)

    # Assertions for the shape of the features dataframe and specific feature columns
    assert features.shape[0] == 3  # 3 rows
    assert 'rolling_mean' in features.columns
    assert 'rolling_std' in features.columns


def test_invalid_dining_hall(mock_dining_predictor):
    """
    Test if invalid dining hall location raises an error in predict_wait_times.
    """
    predictor, _, _, _, _, _ = mock_dining_predictor
    result = predictor.predict_wait_times(datetime(2024, 12, 14, 12, 0), 'InvalidHall')

    # Assert that the result for an invalid hall is None
    assert result is None
