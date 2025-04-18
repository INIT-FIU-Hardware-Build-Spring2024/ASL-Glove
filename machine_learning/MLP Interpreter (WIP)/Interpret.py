import os
import time
import serial
import numpy as np
import joblib
from collections import Counter, deque

from normalizeFunction import normalize  # your helper

# -----------------------------------------------------------------------------
# 1. Load model, scaler, encoder (all in same dir)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model    = joblib.load(os.path.join(BASE_DIR, "gesture_model.pkl"))
scaler   = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
encoder  = joblib.load(os.path.join(BASE_DIR, "label_encoder.pkl"))

print("✅ Loaded:", type(model).__name__)
print("🎯 Expecting", model.n_features_in_, "features")
print("🧠 Classes:", encoder.classes_)

# Grab the exact feature order from scaler
if hasattr(scaler, "feature_names_in_"):
    FEATURE_NAMES = list(scaler.feature_names_in_)
else:
    # fallback if missing
    FEATURE_NAMES = [f"F{i+1}" for i in range(model.n_features_in_)]

# -----------------------------------------------------------------------------
# 2. Open serial port
# -----------------------------------------------------------------------------
ser = serial.Serial("COM4", 9600, timeout=1)
time.sleep(2)

# -----------------------------------------------------------------------------
# 3. Prediction function
# -----------------------------------------------------------------------------
def predict_gesture(raw, threshold=0.45):
    """
    raw: list of 8 floats [F1..F5, X,Y,Z] (raw sensor values)
    returns (gesture_string, confidence_float)
    """
    # normalize each portion exactly as during data collection
    flex_n = normalize(raw[:5], 100, 700)
    imu_n  = normalize(raw[5:],  -1,   2)

    # build a DataFrame so scaler sees valid feature names
    arr = np.array(flex_n + imu_n, dtype=np.float32).reshape(1, -1)
    # wrap in pandas to preserve column names
    import pandas as pd
    df = pd.DataFrame(arr, columns=FEATURE_NAMES)

    # scale
    scaled = scaler.transform(df)

    # predict probabilities
    probs = model.predict_proba(scaled)[0]
    idx   = int(np.argmax(probs))
    conf  = float(probs[idx])
    gest  = encoder.inverse_transform([idx])[0]

    return (gest if conf >= threshold else "Unknown"), conf

# -----------------------------------------------------------------------------
# 4. Live loop + smoothing
# -----------------------------------------------------------------------------
window = deque(maxlen=5)

print("🕹️  Starting gesture interpreter...")

while True:
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line or "Initializing" in line:
            continue

        parts = line.split(",")
        if len(parts) != 8:
            # ignore malformed
            continue

        raw_vals = [float(x) for x in parts]
        gesture, confidence = predict_gesture(raw_vals, threshold=0.75)

        window.append(gesture)
        top, freq = Counter(window).most_common(1)[0]

        # print raw + smoothed
        print(f"Raw Pred: {gesture} ({confidence:.0%})", end=" | ")
        if freq >= 3 and top != "Unknown":
            print(f"Smoothed: {top}")
        else:
            print("Smoothed: Unknown")

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Exiting.")
        break

    except Exception as e:
        # catch-all — print and continue
        print("❌ ERROR:", e)
        continue
