import os
import threading
import time
import serial
import joblib
import numpy as np
import colorsys
import tkinter as tk
from tkinter import ttk
from collections import deque, Counter
from PIL import Image, ImageTk

# ─── 1) Model & Encoder ───────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model    = joblib.load(os.path.join(BASE_DIR, "gesture_model.pkl"))
encoder  = joblib.load(os.path.join(BASE_DIR, "label_encoder.pkl"))

# ─── 2) Serial Setup ─────────────────────────────────────────────────────────
ser = serial.Serial("COM4", 9600, timeout=1)  # adjust your COM port
time.sleep(2)

# ─── 3) Prediction w/ smoothing ──────────────────────────────────────────────
WINDOW = 5
buffer = deque(maxlen=WINDOW)

def predict_confident_gesture(raw_values, threshold):
    arr   = np.array(raw_values, dtype=np.float32).reshape(1, -1)
    probs = model.predict_proba(arr)[0]
    idx   = np.argmax(probs)
    conf  = probs[idx]
    gest  = encoder.inverse_transform([idx])[0]
    return (gest if conf >= threshold else "Unknown"), conf

# ─── 4) Build GUI ────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("🖐 Gesture Interpreter")
root.geometry("800x400")

# ─── 5) Initial Styles & BG ─────────────────────────────────────────────────
bg_color = "#e3a79f"
root.configure(bg=bg_color)

style = ttk.Style()
style.theme_use("default")
style.configure("TFrame", background=bg_color)
style.configure("TLabel", background=bg_color, foreground="white")
style.configure("TButton", padding=5)

# ─── 6) Frames ───────────────────────────────────────────────────────────────
bottom = tk.Frame(root, bg=bg_color, height=120)
bottom.pack(side="bottom", fill="x")

left  = ttk.Frame(root, style="TFrame", padding=10)
left.pack(side="left", fill="y")

right = ttk.Frame(root, style="TFrame", padding=10)
right.pack(side="left", fill="both", expand=True)

# ─── 7) Bottom Logo ─────────────────────────────────────────────────────────
logo_path = os.path.join(BASE_DIR, "signifi_logo.png")
pil_logo  = Image.open(logo_path).convert("RGBA").resize((160, 100), Image.LANCZOS)
signifi_logo = ImageTk.PhotoImage(pil_logo)
logo_lbl = tk.Label(bottom, image=signifi_logo, bg=bg_color, bd=0, highlightthickness=0)
logo_lbl.image = signifi_logo
logo_lbl.pack(pady=10)
logo_lbl.configure(anchor="center")

# ─── 8) Left Controls ───────────────────────────────────────────────────────
raw_var       = tk.StringVar(value="-")
smooth_var    = tk.StringVar(value="-")
conf_var      = tk.DoubleVar(value=0.0)
threshold_var = tk.DoubleVar(value=45.0)

ttk.Label(left, text="Raw Prediction:", font=("Arial",12)).grid(row=0, column=0, sticky="w")
ttk.Label(left, textvariable=raw_var, font=("Arial",16,"bold"), foreground="cyan") \
    .grid(row=1, column=0, sticky="w", pady=(0,10))

ttk.Label(left, text="Confidence:", font=("Arial",12)).grid(row=2, column=0, sticky="w")
pb = ttk.Progressbar(left, variable=conf_var, maximum=100, length=300)
pb.grid(row=3, column=0, sticky="w")
conf_lbl = ttk.Label(left, text="0%", font=("Arial",10))
conf_lbl.grid(row=3, column=1, sticky="w", padx=5)

ttk.Label(left, text="Smoothed Gesture:", font=("Arial",12)).grid(row=4, column=0, sticky="w", pady=(20,0))
ttk.Label(left, textvariable=smooth_var, font=("Arial",16,"bold"), foreground="lime") \
    .grid(row=5, column=0, sticky="w", pady=(0,10))

ttk.Label(left, text="Threshold (%)", font=("Arial",10)).grid(row=6, column=0, sticky="w")
thr_slider = ttk.Scale(left, from_=0, to=100, variable=threshold_var,
                       orient="horizontal", length=300)
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

# ─── 9) Right‑side Images ────────────────────────────────────────────────────
image_label = ttk.Label(right, text="No Image", font=("Arial",14))
image_label.pack(expand=True)

gesture_images = {
    "ILoveYou_New": "iloveyou.png",
    "Paws_Up_New":  "pawsup.png",
    "F_New":        "F.png",
    "I_New":        "I.png",
    "U_New":        "U.png",
    "Water_New":    "water.png",
    "Mom1_New":      "mom.png",
    "Sorry_New":    "sorry.png",
    " Dale_New":     "dale.png"
}
loaded_images = {}
for g, fname in gesture_images.items():
    full = os.path.join(BASE_DIR, fname)
    if os.path.isfile(full):
        pil = Image.open(full).convert("RGBA").resize((200,200), Image.LANCZOS)
        loaded_images[g] = ImageTk.PhotoImage(pil)
    else:
        loaded_images[g] = None

# ─── 10) Animate Pastel Background ──────────────────────────────────────────
hue = 0.0
def animate_bg():
    global hue, bg_color
    hue = (hue + 0.003) % 1.0
    r,g,b = colorsys.hsv_to_rgb(hue, 0.4, 0.9)
    bg_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    root.configure(bg=bg_color)
    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color)
    bottom.configure(bg=bg_color)
    logo_lbl.config(bg=bg_color)
    root.after(50, animate_bg)

animate_bg()

# ─── 11) GUI updater ─────────────────────────────────────────────────────────
def gui_update(raw_pred, smooth, conf):
    raw_var.set(raw_pred)
    smooth_var.set(smooth)
    pct = conf * 100
    conf_var.set(pct)
    conf_lbl.config(text=f"{pct:.0f}%")
    img = loaded_images.get(smooth)
    if img:
        image_label.config(image=img, text="")
        image_label.image = img
    else:
        image_label.config(image="", text="No Image")

# ─── 12) Safe Inference Loop ────────────────────────────────────────────────
running = False

def read_loop():
    try:
        buffer.clear()
        while running:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line or "Initializing" in line:
                time.sleep(0.05)
                continue

            parts = line.split(",")
            if len(parts) != 8:
                time.sleep(0.05)
                continue

            try:
                vals = [float(x) for x in parts]
            except:
                time.sleep(0.05)
                continue

            thresh = threshold_var.get()/100.0
            raw_pred, conf = predict_confident_gesture(vals, thresh)

            buffer.append(raw_pred)
            top, cnt = Counter(buffer).most_common(1)[0]
            smooth = top if (cnt>=3 and top!="Unknown") else "Unknown"
            print("🔍 Smoothed label is:", repr(smooth))

            # schedule UI update on main thread
            root.after(0, lambda rp=raw_pred, sm=smooth, c=conf: gui_update(rp, sm, c))
            time.sleep(0.1)

    except Exception as e:
        print("❌ Read loop crashed:", e)
        root.after(0, stop_reading)

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

root.mainloop()
