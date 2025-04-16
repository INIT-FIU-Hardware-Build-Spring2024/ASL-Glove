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
scaler_pkl = os.path.join(BASE_DIR, "scaler.pkl")
encoder_pkl = os.path.join(BASE_DIR, "label_encoder.pkl")

model = joblib.load(model_pkl)
scaler = joblib.load(scaler_pkl)
encoder = joblib.load(encoder_pkl)

ser = serial.Serial('COM4', 9600) 
print("Model input dtype check:")
print(type(model))
print("Number of features:", model.n_features_in_)
print("First tree type check:", type(model.estimators_[0].tree_.threshold))
print("Tree threshold dtype:", model.estimators_[0].tree_.threshold.dtype)


def predict_confident_gesture(model, scaler, encoder, sensor_input_raw, threshold=0.75):
    try:
        # Convert input to float32
        sensor_input_array = np.array(sensor_input_raw, dtype=np.float32).reshape(1, -1)
        print("Input dtype:", sensor_input_array.dtype)

        # DataFrame for scaler
        sensor_input_df = pd.DataFrame(sensor_input_array, columns=scaler.feature_names_in_)
        scaled_input = scaler.transform(sensor_input_df)

        # Predict probabilities
        probs = model.predict_proba(scaled_input)
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
            gesture = predict_confident_gesture(model, scaler, encoder, parts)
            print("🖐 Gesture Detected:", gesture)
        else:
            print("⚠️ Invalid data format:", line)
    except Exception as e:
        print("❌ Error:", e)


