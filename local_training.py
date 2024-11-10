import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, save_model
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import os
from glob import glob
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_local():
    """Train models locally and save them"""
    dining_halls = ['Dana', 'Roberts', 'Foss']
    sequence_length = 6
    
    # Create ml_models directory if it doesn't exist
    if not os.path.exists('ml_models'):
        os.makedirs('ml_models')
        
    # Load and process multiple CSV files
    print("Loading data...")
    all_data = []
    csv_files = glob('data/October-*.csv')
    
    if not csv_files:
        raise FileNotFoundError("No CSV files found in data directory")
        
    print(f"Found {len(csv_files)} CSV files: {csv_files}")
    
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
                        
                        if location in dining_halls:
                            dt = pd.to_datetime(datetime_str, format='%m/%d/%y %H:%M')
                            records.append({
                                'datetime': dt,
                                'location': location,
                                'count': count
                            })
                    except (ValueError, IndexError) as e:
                        continue
            
            if records:
                df = pd.DataFrame(records)
                all_data.append(df)
                print(f"Processed {len(df)} records from {file}")
                
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            continue
    
    if not all_data:
        raise ValueError("No data was successfully loaded from CSV files")
        
    # Combine all data
    df = pd.concat(all_data, ignore_index=True)
    
    # Add features
    df['hour'] = df['datetime'].dt.hour
    df['minute'] = df['datetime'].dt.minute
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['is_weekend'] = df['datetime'].dt.dayofweek >= 5
    
    # Train model for each dining hall
    for hall in dining_halls:
        print(f"\nTraining model for {hall}...")
        
        # Filter data for this dining hall
        hall_data = df[df['location'] == hall].copy()
        
        # Prepare features
        features = pd.DataFrame({
            'count': hall_data['count'],
            'hour': hall_data['hour'],
            'minute': hall_data['minute'],
            'day_of_week': hall_data['day_of_week'],
            'is_weekend': hall_data['is_weekend'].astype(int)
        })
        
        # Scale features
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(features)
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length):
            X.append(scaled_data[i:(i + sequence_length)])
            y.append(scaled_data[i + sequence_length])
        
        X = np.array(X)
        y = np.array(y)
        
        # Build and train model
        model = Sequential([
            LSTM(64, activation='relu', input_shape=(sequence_length, X.shape[2]), return_sequences=True),
            LSTM(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        print(f"Training model for {hall}...")
        model.fit(
            X, y[:, 0],
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )
        
        print(f"Saving model and scaler for {hall}...")
        model.save(f'ml_models/{hall.lower()}_model.keras')  
        np.save(f'ml_models/{hall.lower()}_scaler.npy', scaler)
        
        print(f"Completed training for {hall}")
        
        # Clear session to free memory
        tf.keras.backend.clear_session()

if __name__ == "__main__":
    print("Starting local model training...")
    train_local()
    print("Training complete!")
