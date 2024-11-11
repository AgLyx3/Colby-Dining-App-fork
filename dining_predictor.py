import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from glob import glob
import os
from datetime import datetime
import logging
import joblib

logger = logging.getLogger(__name__)

class DiningHallPredictor:
    def __init__(self, model_dir='ml_models', data_dir='data'):
        """Initialize predictor with model and data directories"""
        self.dining_halls = ['Dana', 'Roberts', 'Foss']
        self.sequence_length = 6  # Keep for feature engineering
        self.models = {}
        self.scalers = {}
        self.model_dir = model_dir
        self.data_dir = data_dir
        
        # Create required directories if they don't exist
        for directory in [model_dir, data_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
            
        # Try to load existing models
        self.load_saved_models()
        
    def load_saved_models(self):
        """Load pre-trained models if they exist"""
        for hall in self.dining_halls:
            model_path = os.path.join(self.model_dir, f'{hall.lower()}_model.joblib')
            scaler_path = os.path.join(self.model_dir, f'{hall.lower()}_scaler.joblib')
            
            try:
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.models[hall] = joblib.load(model_path)
                    self.scalers[hall] = joblib.load(scaler_path)
                    logger.info(f"Loaded saved model for {hall}")
            except Exception as e:
                logger.error(f"Error loading model for {hall}: {str(e)}")
                
    def save_models(self):
        """Save trained models and scalers"""
        for hall in self.dining_halls:
            if hall in self.models and hall in self.scalers:
                try:
                    model_path = os.path.join(self.model_dir, f'{hall.lower()}_model.joblib')
                    scaler_path = os.path.join(self.model_dir, f'{hall.lower()}_scaler.joblib')
                    
                    joblib.dump(self.models[hall], model_path)
                    joblib.dump(self.scalers[hall], scaler_path)
                    logger.info(f"Saved model for {hall}")
                except Exception as e:
                    logger.error(f"Error saving model for {hall}: {str(e)}")

    def load_data(self, csv_pattern='October-*.csv'):
        """Load and combine data from multiple CSV files"""
        # Update the path to look in the data directory
        data_path = os.path.join(self.data_dir, csv_pattern)
        logger.info(f"Loading data from pattern: {data_path}")
        
        csv_files = glob(data_path)
        logger.info(f"Found {len(csv_files)} CSV files: {csv_files}")
        
        if len(csv_files) == 0:
            raise ValueError(f"No CSV files found in {self.data_dir} matching pattern {csv_pattern}")
        
        # Initialize the all_data list
        all_data = []  
        
        for file in csv_files:
            try:
                with open(file, 'r') as f:
                    lines = f.readlines()
                
                records = []
                for line in lines:
                    if 'Grand Total' in line:
                        continue
                    
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    for i in range(0, len(parts)-2, 3):
                        try:
                            datetime_str = parts[i]
                            location = parts[i+1]
                            count = int(parts[i+2])
                            
                            if location in self.dining_halls:
                                dt = pd.to_datetime(datetime_str, format='%m/%d/%y %H:%M')
                                records.append({
                                    'datetime': dt,
                                    'location': location,
                                    'count': count
                                })
                        except (ValueError, IndexError):
                            continue
                
                if records:
                    df = pd.DataFrame(records)
                    all_data.append(df)
                
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
                continue
        
        if not all_data:
            raise ValueError("No data was successfully loaded from any CSV file")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Add features
        combined_df['day_of_week'] = combined_df['datetime'].dt.dayofweek
        combined_df['hour'] = combined_df['datetime'].dt.hour
        combined_df['minute'] = combined_df['datetime'].dt.minute
        combined_df['is_weekend'] = combined_df['datetime'].dt.dayofweek >= 5
        combined_df['time_of_day'] = combined_df['hour'] + combined_df['minute']/60
        combined_df['is_peak_hour'] = combined_df['hour'].isin([8, 12, 18])
        
        return combined_df.sort_values('datetime')

    def prepare_features(self, data):
        """Prepare features for model training"""
        features = pd.DataFrame({
            'count': data['count'],
            'hour': data['hour'],
            'minute': data['minute'],
            'day_of_week': data['day_of_week'],
            'is_weekend': data['is_weekend'].astype(int),
            'time_of_day': data['time_of_day'],
            'is_peak_hour': data['is_peak_hour'].astype(int)
        })
        
        # Add rolling statistics for the sequence length
        features['rolling_mean'] = features['count'].rolling(self.sequence_length, min_periods=1).mean()
        features['rolling_std'] = features['count'].rolling(self.sequence_length, min_periods=1).std()
        
        return features.fillna(method='bfill').fillna(method='ffill')

    def train_models(self, df, save=True):
        """Train models with option to save"""
        logger.info("Starting model training")
        
        for hall in self.dining_halls:
            try:
                logger.info(f"Training model for {hall}")
                
                # Filter data
                hall_data = df[df['location'] == hall].copy()
                if len(hall_data) == 0:
                    logger.warning(f"No data found for {hall}")
                    continue
                
                # Prepare features
                features = self.prepare_features(hall_data)
                
                # Scale features
                scaler = MinMaxScaler()
                scaled_data = scaler.fit_transform(features)
                
                # Split data
                train_size = int(len(scaled_data) * 0.8)
                X_train = scaled_data[:train_size]
                y_train = hall_data['count'].values[:train_size]
                
                # Train model
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                )
                model.fit(X_train, y_train)
                
                # Store model and scaler
                self.models[hall] = model
                self.scalers[hall] = scaler
                
                if save:
                    self.save_models()
                
                logger.info(f"Successfully trained model for {hall}")
                
            except Exception as e:
                logger.error(f"Error training model for {hall}: {str(e)}")
                continue

    def predict_wait_times(self, current_time, location):
        """Predict wait times based on dining hall swipe data."""
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
            
            # Create feature vector for prediction
            features = pd.DataFrame([{
                'count': 0,  # Placeholder for scaling
                'hour': current_time.hour,
                'minute': current_time.minute,
                'day_of_week': current_time.weekday(),
                'is_weekend': current_time.weekday() >= 5,
                'time_of_day': current_time.hour + current_time.minute/60,
                'is_peak_hour': current_time.hour in [8, 12, 18],
                'rolling_mean': 0,  # Will be scaled
                'rolling_std': 0  # Will be scaled
            }])
            
            # Scale features
            scaled_features = self.scalers[location].transform(features)
            
            # Make prediction
            predicted_swipes = self.models[location].predict(scaled_features)[0]
            predicted_swipes = int(max(0, predicted_swipes))  # Ensure non-negative
            
            # Calculate swipes per minute
            swipes_per_minute = predicted_swipes / 15
            
            # Calculate wait time based on traffic level
            if swipes_per_minute > 2.67:  # >40 swipes per 15 min (high traffic)
                wait_time = (predicted_swipes * 10) / 60  # 10 seconds per swipe
                busyness_level = 'High'
            elif swipes_per_minute > 1.33:  # 20-40 swipes per 15 min (medium traffic)
                wait_time = (predicted_swipes * 7) / 60  # 7 seconds per swipe
                busyness_level = 'Medium'
            else:  # <20 swipes per 15 min (low traffic)
                wait_time = (predicted_swipes * 5) / 60  # 5 seconds per swipe
                busyness_level = 'Low'
            
            # Add small random variation (±10%) to make predictions more realistic
            variation = np.random.uniform(0.9, 1.1)
            wait_time = round(wait_time * variation, 1)
            
            # Cap maximum wait at 15 minutes
            wait_time = min(wait_time, 15)
            
            return {
                'predicted_count': predicted_swipes,
                'wait_time_minutes': wait_time,
                'swipes_per_minute': round(swipes_per_minute, 2),
                'busyness_level': busyness_level,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error predicting for {location}: {str(e)}")
            return None

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get the directory containing this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Initialize predictor with paths relative to the script location
        predictor = DiningHallPredictor(
            model_dir=os.path.join(base_dir, 'ml_models'),
            data_dir=os.path.join(base_dir, 'data')
        )
        
        # Check if we have saved models
        if not any(predictor.models):
            logger.info("No saved models found, training new models...")
            df = predictor.load_data('October-*.csv')
            predictor.train_models(df, save=True)
        
        # Make predictions for all dining halls
        current_time = datetime.now()
        logger.info(f"\nGenerating predictions for {current_time.strftime('%I:%M %p')}")
        
        print("\n" + "="*50)
        print(f"Dining Hall Predictions for {current_time.strftime('%I:%M %p')}")
        print("="*50)
        
        for hall in predictor.dining_halls:
            prediction = predictor.predict_wait_times(current_time, hall)
            print(f"\n{hall}:")
            if prediction:
                if prediction.get('status') == 'closed':
                    print(f"  Status: {prediction['message']}")
                else:
                    print(f"  Expected crowd: {prediction['predicted_count']} people")
                    print(f"  Estimated wait: {prediction['wait_time_minutes']} minutes")
                    print(f"  Traffic level: {prediction['busyness_level']}")
            else:
                print("  Status: Error generating prediction")
                
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")