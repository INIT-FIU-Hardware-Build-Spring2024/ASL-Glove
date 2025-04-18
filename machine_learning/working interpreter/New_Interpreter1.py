import serial
import numpy as np
import pandas as pd 
import joblib
from collections import Counter
import os
print("Current working directory:", os.getcwd())

#ensures that the pkl files are read without having to specifically declare path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_pkl = os.path.join(BASE_DIR, "gesture_model.pkl")
encoder_pkl = os.path.join(BASE_DIR, "label_encoder.pkl")

model = joblib.load(model_pkl)
encoder = joblib.load(encoder_pkl)

ser = serial.Serial('COM4', 9600) 
print("Model input dtype check:")
print(type(model))
print("Number of features:", model.n_features_in_)
print("First tree type check:", type(model.estimators_[0].tree_.threshold))
print("Tree threshold dtype:", model.estimators_[0].tree_.threshold.dtype)


def predict_confident_gesture(model, encoder, sensor_input_raw, threshold=0.75):
    try:
        # Make a copy of the input data so we don't modify the original
        sensor_input_fixed = sensor_input_raw.copy()
        
        # Convert input to float32 and reshape to match model input
        sensor_input_array = np.array(sensor_input_fixed, dtype=np.float32).reshape(1, -1)
        print("Input dtype:", sensor_input_array.dtype)
        print("Input shape:", sensor_input_array.shape)

        # No scaling needed - use the array directly
        # Predict probabilities
        probs = model.predict_proba(sensor_input_array)
        pred_index = np.argmax(probs)
        confidence = probs[0][pred_index]
        gesture = encoder.inverse_transform([pred_index])[0]

        print(f"Prediction: {gesture} | Confidence: {confidence:.2f}")

        if confidence >= threshold:
            return gesture
        else:
            return "Unknown"

    except Exception as e:
        print("❌ Prediction error:", e)
        return "Error"

# Initialize for majority voting
recent_predictions = []
WINDOW_SIZE = 5  # Number of predictions to consider

while True:
    line = ser.readline().decode('utf-8').strip()
    print(f"Raw line from glove: '{line}'")
    
    # Skip any lines that aren't valid sensor data
    if not any(char.isdigit() for char in line) or "Initializing" in line:
        print("Ignored:", line)
        continue

    try:
        parts = [float(x.strip()) for x in line.split(",")]
        if len(parts) == 8:
            gesture = predict_confident_gesture(model, encoder, parts)
            
            # Optional: Add majority voting for more stable predictions
            recent_predictions.append(gesture)
            if len(recent_predictions) > WINDOW_SIZE:
                recent_predictions.pop(0)
            
            if len(recent_predictions) == WINDOW_SIZE:
                # Only consider valid predictions (not "Unknown" or "Error")
                valid_predictions = [p for p in recent_predictions 
                                   if not (p.startswith("Unknown") or p.startswith("Error"))]
                
                if valid_predictions:
                    counter = Counter(valid_predictions)
                    majority_gesture, count = counter.most_common(1)[0]
                    
                    # Only accept majority if it appears more than once
                    if count > 1:
                        print("🖐 Gesture Detected:", majority_gesture, f"(majority {count}/{WINDOW_SIZE})")
                    else:
                        print("🖐 Gesture Detected:", gesture, "(single prediction)")
                else:
                    print("🖐 Gesture Detected:", gesture, "(no valid majority)")
            else:
                print("🖐 Gesture Detected:", gesture)
        else:
            print("⚠️ Invalid data format:", line)
    except Exception as e:
        print("❌ Error:", e)