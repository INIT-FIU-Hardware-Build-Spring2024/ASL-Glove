import os
import tkinter as tk
from tkinter import ttk
import serial, joblib, numpy as np, threading, time
from collections import deque, Counter
from PIL import Image, ImageTk
from normalizeFunction import normalize
import colorsys

# ─── 1) Load Model Artifacts ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model    = joblib.load(os.path.join(BASE_DIR, "gesture_model.pkl"))
scaler   = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
encoder  = joblib.load(os.path.join(BASE_DIR, "label_encoder.pkl"))

# ─── 2) Serial Port Setup ─────────────────────────────────────────────────────
ser = serial.Serial("COM4", 9600, timeout=1)
time.sleep(2)

# ─── 3) Prediction Function ───────────────────────────────────────────────────
def predict_gesture(raw_values, threshold):
    flex_n = normalize(raw_values[:5], 100, 700)
    imu_n  = normalize(raw_values[5:],  -1,   2)
    arr    = np.array(flex_n + imu_n, dtype=np.float32).reshape(1, -1)
    arr_scl= scaler.transform(arr)

    probs  = model.predict_proba(arr_scl)[0]
    idx    = np.argmax(probs)
    conf   = probs[idx]
    gest   = encoder.inverse_transform([idx])[0]
    return (gest, conf) if conf >= threshold else ("Unknown", conf)

# ─── 4) Build Main Window ─────────────────────────────────────────────────────
root = tk.Tk()
root.title("🖐 Gesture Interpreter")
root.geometry("800x400")

# ─── 5) Initial Styles & BG ───────────────────────────────────────────────────
bg_color = "#e3a79f"   # pastel background
root.configure(bg=bg_color)

style = ttk.Style()
style.theme_use("default")
style.configure("TFrame",  background=bg_color)
style.configure("TLabel",  background=bg_color, foreground="white")
style.configure("TButton", padding=5)

# ─── 6) Load Gesture Images (after root exists!) ─────────────────────────────
gesture_images = {
    "ILoveYou": "iloveyou.png",
    "Paws_Up":  "pawsup.png",
    "Dale":     "dale.png"
}
loaded_images = {}
for gesture, fname in gesture_images.items():
    path = os.path.join(BASE_DIR, fname)
    if os.path.isfile(path):
        try:
            pil = Image.open(path).convert("RGBA")
            loaded_images[gesture] = ImageTk.PhotoImage(pil)
            pil = pil.resize((250, 400), Image.LANCZOS)
            loaded_images[gesture] = ImageTk.PhotoImage(pil)
        except Exception as e:
            print(f"❌ Could not load '{fname}': {e}")
            loaded_images[gesture] = None
    else:
        print(f"⚠️ Missing '{fname}'")
        loaded_images[gesture] = None

# ─── 7) Load & resize Signifi Logo ────────────────────────────────────────────
logo_path = os.path.join(BASE_DIR, "signifi_logo.png")
if not os.path.isfile(logo_path):
    raise FileNotFoundError(f"Cannot find logo at '{logo_path}'")
pil_logo     = Image.open(logo_path).convert("RGBA")
pil_logo     = pil_logo.resize((160, 100), Image.LANCZOS)
signifi_logo = ImageTk.PhotoImage(pil_logo)

# ─── 8) Layout Frames ─────────────────────────────────────────────────────────
bottom = tk.Frame(root, bg=bg_color, height=120)
bottom.pack(side="bottom", fill="x")

left   = ttk.Frame(root, style="TFrame", padding=10)
left.pack(side="left", fill="y")

right  = ttk.Frame(root, style="TFrame", padding=10)
right.pack(side="left", fill="both", expand=True)

# ─── 9) Place centered logo in bottom ────────────────────────────────────────
logo_lbl = tk.Label(bottom,
                    image=signifi_logo,
                    bg=bg_color,
                    bd=0,
                    highlightthickness=0)
logo_lbl.image = signifi_logo
logo_lbl.pack(pady=10)             # pack w/o fill => centers itself
logo_lbl.configure(anchor="center")

# ───10) Left‑side Controls ────────────────────────────────────────────────────
raw_var       = tk.StringVar(value="-")
conf_var      = tk.DoubleVar(value=0.0)
smooth_var    = tk.StringVar(value="-")
threshold_var = tk.DoubleVar(value=45.0)

ttk.Label(left, text="Raw Prediction:", font=("Arial",12)) \
   .grid(row=0, column=0, sticky="w")
ttk.Label(left, textvariable=raw_var,
    font=("Arial",16,"bold"), foreground="cyan") \
   .grid(row=1, column=0, sticky="w", pady=(0,10))

ttk.Label(left, text="Confidence:", font=("Arial",12)) \
   .grid(row=2, column=0, sticky="w")
pb = ttk.Progressbar(left, variable=conf_var, maximum=100, length=300)
pb.grid(row=3, column=0, sticky="w")
conf_lbl = ttk.Label(left, text="0%", font=("Arial",10))
conf_lbl.grid(row=3, column=1, sticky="w", padx=5)

ttk.Label(left, text="Smoothed Gesture:", font=("Arial",12)) \
   .grid(row=4, column=0, sticky="w", pady=(20,0))
ttk.Label(left, textvariable=smooth_var,
    font=("Arial",16,"bold"), foreground="lime") \
   .grid(row=5, column=0, sticky="w", pady=(0,10))

ttk.Label(left, text="Threshold (%)", font=("Arial",10)) \
   .grid(row=6, column=0, sticky="w")
thr_slider = ttk.Scale(left, from_=0, to=100,
    variable=threshold_var, orient="horizontal", length=300)
thr_slider.grid(row=7, column=0, sticky="w")
thr_disp = ttk.Label(left, textvariable=threshold_var)
thr_disp.grid(row=7, column=1, sticky="w", padx=5)

btn_frame = ttk.Frame(left, style="TFrame")
btn_frame.grid(row=8, column=0, pady=20)
start_btn = ttk.Button(btn_frame, text="▶ Start")
stop_btn  = ttk.Button(btn_frame, text="■ Stop")
start_btn.pack(side="left", padx=5)
stop_btn.pack(side="left", padx=5)
stop_btn.state(["disabled"])

# ───11) Right‑side Placeholder ────────────────────────────────────────────────
image_label = ttk.Label(right, text="No Image", font=("Arial",14))
image_label.pack(expand=True)

# ───12) Pastel Rainbow Background ─────────────────────────────────────────────
hue = 0.0
def animate_bg():
    global hue, bg_color
    hue = (hue + 0.003) % 1.0
    r,g,b = colorsys.hsv_to_rgb(hue, 0.4, 0.9)
    bg_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    # update colors
    root.configure(bg=bg_color)
    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color)
    bottom.configure(bg=bg_color)
    logo_lbl.config(bg=bg_color)
    root.after(50, animate_bg)

animate_bg()

# ───13) Inference Loop ────────────────────────────────────────────────────────
window, running = deque(maxlen=5), False

def read_loop():
    global running
    window.clear()
    while running:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line or "Initializing" in line:
            continue
        parts = line.split(",")
        if len(parts) != 8: 
            continue
        try:
            raw_vals = [float(x) for x in parts]
        except:
            continue

        pred, conf = predict_gesture(raw_vals, threshold_var.get()/100.0)
        raw_var.set(pred)
        conf_var.set(conf*100)
        conf_lbl.config(text=f"{conf*100:.0f}%")

        window.append(pred)
        top, freq = Counter(window).most_common(1)[0]
        sm = top if (freq>=3 and top!="Unknown") else "Unknown"
        smooth_var.set(sm)

        img = loaded_images.get(sm)
        if img:
            image_label.config(image=img, text="")
            image_label.image = img
        else:
            image_label.config(image="", text="No Image\nAvailable")

        time.sleep(0.1)

def start_reading():
    global running
    if not running:
        running = True
        start_btn.state(["disabled"])
        stop_btn.state(["!disabled"])
        threading.Thread(target=read_loop, daemon=True).start()

def stop_reading():
    global running
    running = False
    start_btn.state(["!disabled"])
    stop_btn.state(["disabled"])

start_btn.config(command=start_reading)
stop_btn.config(command=stop_reading)

# ───14) Launch GUI ────────────────────────────────────────────────────────────
root.mainloop()
