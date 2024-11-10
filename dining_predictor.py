import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DiningHallPredictor:
    def __init__(self, model_dir='ml_models'):
        """Initialize predictor with model directory for pre-trained models"""
        self.dining_halls = ['Dana', 'Roberts', 'Foss']
        self.sequence_length = 6
        self.models = {}
        self.scalers = {}
        self.model_dir = model_dir
        
        # Create model directory if it doesn't exist
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            
        # Load pre-trained models
        self.load_saved_models()

    def load_saved_models(self):
        """Load pre-trained models if they exist"""
        for hall in self.dining_halls:
            model_path = os.path.join(self.model_dir, f'{hall.lower()}_model.keras')
            scaler_path = os.path.join(self.model_dir, f'{hall.lower()}_scaler.npy')
            
            try:
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.models[hall] = load_model(model_path)
                    self.scalers[hall] = np.load(scaler_path, allow_pickle=True).item()
                    logger.info(f"Loaded saved model for {hall}")
                else:
                    logger.warning(f"No saved model found for {hall} at {model_path}")
            except Exception as e:
                logger.error(f"Error loading model for {hall}: {str(e)}")

    def predict_wait_times(self, current_time, location):
        """
        Predict wait times for a given location and time using pre-trained models
        
        Parameters:
        - current_time: datetime object
        - location: str, dining hall name
        
        Returns: dict with predictions or None if error
        """
        try:
            # Validate inputs
            if location not in self.dining_halls:
                logger.error(f"Invalid location: {location}")
                return None
                
            if location not in self.models or location not in self.scalers:
                logger.error(f"No model available for {location}")
                return None
            
            # Operating hours check (7 AM to 8 PM)
            if current_time.hour < 7 or current_time.hour >= 20:
                logger.info(f"{location} is closed at {current_time.hour}:00")
                return {
                    'status': 'closed',
                    'message': 'Dining hall is currently closed'
                }
            
            # Create feature vector
            features = pd.DataFrame({
                'count': [0],  # Placeholder for scaling
                'hour': [current_time.hour],
                'minute': [current_time.minute],
                'day_of_week': [current_time.weekday()],
                'is_weekend': [current_time.weekday() >= 5]
            })
            
            # Scale features
            scaled_features = self.scalers[location].transform(features)
            
            # Prepare sequence for LSTM
            sequence = np.repeat(scaled_features, self.sequence_length, axis=0)
            model_input = sequence.reshape(1, self.sequence_length, scaled_features.shape[1])
            
            # Make prediction
            prediction = self.models[location].predict(model_input, verbose=0)
            
            # Process prediction
            predicted_count = int(max(0, self.scalers[location].inverse_transform(
                np.hstack((prediction, scaled_features[0, 1:].reshape(1, -1)))
            )[0, 0]))
            
            # Calculate wait time based on predicted crowd
            if predicted_count > 50:  # High traffic
                wait_time = predicted_count * 1.5
            elif predicted_count >= 10:  # Normal traffic
                wait_time = predicted_count * 1.0
            else:  # Low traffic
                wait_time = predicted_count * 0.5
            
            # Cap wait time at 30 minutes and ensure minimum of 0.5 minutes
            wait_time = min(30, max(0.5, wait_time))
            
            logger.info(f"Prediction for {location}: {predicted_count} people, {wait_time:.1f} minutes wait")
            
            return {
                'predicted_count': predicted_count,
                'wait_time_minutes': round(wait_time, 1),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error predicting for {location}: {str(e)}")
            return None

    def get_model_info(self):
        """Get information about loaded models"""
        info = {}
        for hall in self.dining_halls:
            info[hall] = {
                'model_loaded': hall in self.models,
                'scaler_loaded': hall in self.scalers
            }
        return info

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test predictions
    try:
        predictor = DiningHallPredictor()
        
        # Print model loading status
        model_info = predictor.get_model_info()
        print("\nModel Loading Status:")
        for hall, status in model_info.items():
            print(f"{hall}: {status}")
        
        # Make test predictions
        current_time = datetime.now()
        print(f"\nMaking test predictions for {current_time.strftime('%I:%M %p')}:")
        
        for hall in predictor.dining_halls:
            prediction = predictor.predict_wait_times(current_time, hall)
            if prediction:
                if prediction.get('status') == 'closed':
                    print(f"\n{hall}: {prediction['message']}")
                else:
                    print(f"\n{hall}:")
                    print(f"Expected crowd: {prediction['predicted_count']} people")
                    print(f"Estimated wait: {prediction['wait_time_minutes']} minutes")
            else:
                print(f"\n{hall}: Prediction failed")
                
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
