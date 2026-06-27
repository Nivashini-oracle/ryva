# =============================================================
# RYVA Project — main_loop.py
# Purpose : Links face_pipeline.py + cls_engine.py together
#           Thread 1 → captures frames, runs face pipeline
#           Thread 2 → reads queue, computes CLS every second
# Author  : RYVA Team
# Usage   : python main_loop.py
# Done When:
#   Sit normally     → CLS stays below 40 (GREEN)
#   Close eyes 30s   → CLS climbs above 41 (AMBER)
#   Prints once per second without crashing
# =============================================================

import cv2
import time
import queue
import threading
import collections
import sys
import os

# --- Import RYVA modules ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vision.face_pipeline import FacePipeline
from cognitive_engine.cls_engine import compute_cls, get_cls_band, DEFAULT_BASELINE

# ==============================================================
# CONFIGURATION
# ==============================================================

# Placeholders until Arduino (ESP32) is connected in Week 2
PLACEHOLDER_MOVEMENT_VAR = 10.0   # MPU6050 not connected yet
PLACEHOLDER_TEMP         = 30.0   # DHT11 not connected yet
PLACEHOLDER_VIB          = False  # Vibration sensor not connected yet

# CLS computed once per second
CLS_INTERVAL = 1.0

# Rolling window for averaging face metrics (25 frames = 1 second)
WINDOW_SIZE = 25

# Queue between vision thread and CLS thread
frame_queue = queue.Queue(maxsize=5)

# Shared state between threads (thread-safe using lock)
latest_metrics = {
    "ear"        : 0.30,
    "head_pitch" : 5.0,
    "blink_rate" : 15.0,
    "gaze"       : "CENTER"
}
metrics_lock = threading.Lock()

# Stop signal for both threads
stop_event = threading.Event()


# ==============================================================
# THREAD 1 — VISION THREAD
# Captures frames → runs FacePipeline → writes metrics to queue
# ==============================================================

def vision_thread():
    """
    Runs at 25fps.
    Captures camera frames, processes through FacePipeline,
    and puts face metrics into the shared queue.
    """
    print("[Vision] Starting camera...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[Vision] ERROR — Could not open camera.")
        stop_event.set()
        return

    pipeline   = FacePipeline()
    target_fps = 25
    interval   = 1.0 / target_fps
    last_time  = time.time()

    # Rolling windows for smoothing
    ear_window   = collections.deque(maxlen=WINDOW_SIZE)
    pitch_window = collections.deque(maxlen=WINDOW_SIZE)
    blink_times  = collections.deque(maxlen=WINDOW_SIZE)

    print("[Vision] Camera ready ✅")

    while not stop_event.is_set():

        # --- FPS throttle ---
        now = time.time()
        if (now - last_time) < interval:
            continue
        last_time = now

        ret, frame = cap.read()
        if not ret:
            print("[Vision] WARNING — Frame read failed.")
            continue

        # --- Run face pipeline ---
        metrics = pipeline.process_frame(frame)

        if metrics:
            ear_window.append(metrics["ear"])
            pitch_window.append(metrics["pitch"])

            if metrics["blink"]:
                blink_times.append(time.time())

            # Blink rate = blinks in last 60 seconds
            now_t      = time.time()
            recent     = [t for t in blink_times if now_t - t <= 60]
            blink_rate = len(recent)

            # Smoothed averages
            avg_ear   = sum(ear_window)   / len(ear_window)
            avg_pitch = sum(pitch_window) / len(pitch_window)

            # Write to shared state
            with metrics_lock:
                latest_metrics["ear"]        = round(avg_ear,   3)
                latest_metrics["head_pitch"] = round(avg_pitch, 2)
                latest_metrics["blink_rate"] = blink_rate
                latest_metrics["gaze"]       = metrics["gaze"]

        # --- Show camera window (optional debug) ---
        if metrics:
            pipeline.draw_metrics(frame, metrics)
        cv2.imshow("RYVA — Vision", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[Vision] Quit signal received.")
            stop_event.set()
            break

    cap.release()
    pipeline.release()
    cv2.destroyAllWindows()
    print("[Vision] Thread stopped.")


# ==============================================================
# THREAD 2 — CLS THREAD
# Reads face metrics every second → computes CLS → prints result
# ==============================================================

def cls_thread():
    """
    Runs every 1 second.
    Reads latest face metrics, adds placeholder biosignals,
    computes CLS score, and prints result to terminal.
    """
    print("[CLS] Engine started ✅")
    time.sleep(2)  # Wait for vision thread to warm up

    band_colors = {
        "GREEN" : "🟢",
        "AMBER" : "🟡",
        "RED"   : "🔴"
    }

    while not stop_event.is_set():
        loop_start = time.time()

        # --- Read latest face metrics (thread-safe) ---
        with metrics_lock:
            ear        = latest_metrics["ear"]
            head_pitch = latest_metrics["head_pitch"]
            blink_rate = latest_metrics["blink_rate"]
            gaze       = latest_metrics["gaze"]

        # --- Add placeholders (Arduino not connected yet) ---
        movement_var = PLACEHOLDER_MOVEMENT_VAR
        temp         = PLACEHOLDER_TEMP

        # --- Compute CLS ---
        score = compute_cls(
            ear          = ear,
            head_pitch   = head_pitch,
            blink_rate   = blink_rate,
            movement_var = movement_var,
            temp         = temp,
            baseline     = DEFAULT_BASELINE
        )

        band  = get_cls_band(score)
        emoji = band_colors[band]

        # --- Print to terminal ---
        print(
            f"{emoji} CLS: {score:<6} | "
            f"State: {band:<6} | "
            f"EAR: {ear:<6} | "
            f"Pitch: {head_pitch:<6} | "
            f"Blinks: {blink_rate:<4} | "
            f"Gaze: {gaze}"
        )

        # --- Wait for next second ---
        elapsed = time.time() - loop_start
        sleep_time = max(0, CLS_INTERVAL - elapsed)
        time.sleep(sleep_time)

    print("[CLS] Thread stopped.")


# ==============================================================
# MAIN — Start both threads
# ==============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  RYVA — Main Loop")
    print("  Face Pipeline + CLS Engine")
    print("  Press 'q' in camera window to quit")
    print("=" * 60)
    print()
    print(f"  Placeholders active:")
    print(f"  movement_var = {PLACEHOLDER_MOVEMENT_VAR} (ESP32 not connected)")
    print(f"  temp         = {PLACEHOLDER_TEMP}°C (DHT11 not connected)")
    print()
    print("-" * 60)
    print(f"  {'CLS':<8} {'State':<8} {'EAR':<8} {'Pitch':<8} {'Blinks':<8} Gaze")
    print("-" * 60)

    # --- Start Vision Thread ---
    t1 = threading.Thread(target=vision_thread, name="VisionThread", daemon=True)

    # --- Start CLS Thread ---
    t2 = threading.Thread(target=cls_thread, name="CLSThread", daemon=True)

    t1.start()
    t2.start()

    # --- Keep main thread alive until quit ---
    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Main] Keyboard interrupt — stopping...")
        stop_event.set()

    t1.join(timeout=3)
    t2.join(timeout=3)

    print("\n[Main] RYVA stopped cleanly. ✅")
