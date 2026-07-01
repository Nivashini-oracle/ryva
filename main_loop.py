# =============================================================
# RYVA Project — main_loop.py  (updated g-7)
# Purpose : Links face pipeline + serial receiver + CLS engine
#           Broadcasts CLS updates to dashboard via WebSocket
# Author  : RYVA Team
# Usage   : python main_loop.py
# NOTE    : Start ws_server.py FIRST before running this
# Done When:
#   Dashboard gauge updates every second from real Arduino data
#   Move wrist quickly → movement_var rises → CLS rises
# =============================================================

import cv2
import time
import queue
import threading
import collections
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision.face_pipeline              import FacePipeline
from cognitive_engine.cls_engine       import compute_cls, get_cls_band, DEFAULT_BASELINE
from biosignal.serial_receiver         import serial_receiver

# ==============================================================
# CONFIGURATION
# ==============================================================

CLS_INTERVAL = 1.0
WINDOW_SIZE  = 25

# ==============================================================
# SHARED STATE
# ==============================================================

latest_face = {
    "ear"        : 0.30,
    "head_pitch" : 5.0,
    "blink_rate" : 15.0,
    "gaze"       : "CENTER"
}
face_lock = threading.Lock()

serial_state = {
    "movement_var" : 10.0,
    "temp"         : 30.0,
    "hum"          : 60.0,
    "vib"          : False
}
serial_lock = threading.Lock()

stop_event = threading.Event()
ws_loop    = None


# ==============================================================
# THREAD 1 — VISION THREAD
# ==============================================================

def vision_thread():
    print("[Vision] Starting camera...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[Vision] ERROR — Could not open camera.")
        stop_event.set()
        return

    pipeline     = FacePipeline()
    interval     = 1.0 / 25
    last_time    = time.time()
    ear_window   = collections.deque(maxlen=WINDOW_SIZE)
    pitch_window = collections.deque(maxlen=WINDOW_SIZE)
    blink_times  = collections.deque(maxlen=WINDOW_SIZE)

    print("[Vision] Camera ready ✅")

    while not stop_event.is_set():
        now = time.time()
        if (now - last_time) < interval:
            continue
        last_time = now

        ret, frame = cap.read()
        if not ret:
            continue

        metrics = pipeline.process_frame(frame)

        if metrics:
            ear_window.append(metrics["ear"])
            pitch_window.append(metrics["pitch"])

            if metrics["blink"]:
                blink_times.append(time.time())

            now_t      = time.time()
            recent     = [t for t in blink_times if now_t - t <= 60]
            blink_rate = len(recent)
            avg_ear    = sum(ear_window)   / len(ear_window)
            avg_pitch  = sum(pitch_window) / len(pitch_window)

            with face_lock:
                latest_face["ear"]        = round(avg_ear,   3)
                latest_face["head_pitch"] = round(avg_pitch, 2)
                latest_face["blink_rate"] = blink_rate
                latest_face["gaze"]       = metrics["gaze"]

        pipeline.draw_metrics(frame, metrics)
        cv2.imshow("RYVA — Vision", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    cap.release()
    pipeline.release()
    cv2.destroyAllWindows()
    print("[Vision] Thread stopped.")


# ==============================================================
# THREAD 2 — BIOSIGNAL THREAD
# ==============================================================

def biosignal_thread():
    print("[Biosignal] Starting serial receiver...")
    q = queue.Queue(maxsize=10)

    threading.Thread(
        target=serial_receiver,
        args=(q, stop_event),
        name="SerialReceiverThread",
        daemon=True
    ).start()

    while not stop_event.is_set():
        try:
            data = q.get(timeout=2)
            with serial_lock:
                serial_state.update(data)
        except queue.Empty:
            continue

    print("[Biosignal] Thread stopped.")


# ==============================================================
# THREAD 3 — CLS THREAD
# ==============================================================

def cls_thread():
    print("[CLS] Engine started ✅")
    time.sleep(2)

    band_colors = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}

    while not stop_event.is_set():
        loop_start = time.time()

        with face_lock:
            ear        = latest_face["ear"]
            head_pitch = latest_face["head_pitch"]
            blink_rate = latest_face["blink_rate"]
            gaze       = latest_face["gaze"]

        with serial_lock:
            s = serial_state.copy()

        movement_var = s["movement_var"]
        temp         = s["temp"]
        hum          = s["hum"]
        vib          = s["vib"]

        # Vibration reduces movement_var weight by 60%
        move_weight  = 0.4 if vib else 1.0
        adjusted_var = movement_var * move_weight

        score = compute_cls(
            ear          = ear,
            head_pitch   = head_pitch,
            blink_rate   = blink_rate,
            movement_var = adjusted_var,
            temp         = temp,
            baseline     = DEFAULT_BASELINE
        )

        band  = get_cls_band(score)
        emoji = band_colors[band]
        vib_str = "⚡VIB" if vib else "    "

        print(
            f"{emoji} CLS: {score:<6} | "
            f"State: {band:<6} | "
            f"EAR: {ear:<6} | "
            f"Pitch: {head_pitch:<6} | "
            f"Temp: {temp}°C | "
            f"Var: {movement_var:<6} | "
            f"{vib_str}"
        )

        # Broadcast to WebSocket dashboard
        payload = {
            "cls_score"    : score,
            "band"         : band,
            "ear"          : ear,
            "head_pitch"   : head_pitch,
            "blink_rate"   : blink_rate,
            "gaze"         : gaze,
            "temp"         : temp,
            "hum"          : hum,
            "movement_var" : movement_var,
            "vib"          : vib,
            "timestamp"    : time.time()
        }

        if ws_loop and ws_loop.is_running():
            try:
                from ws_server import broadcast
                asyncio.run_coroutine_threadsafe(broadcast(payload), ws_loop)
            except Exception:
                pass

        elapsed    = time.time() - loop_start
        time.sleep(max(0, CLS_INTERVAL - elapsed))

    print("[CLS] Thread stopped.")


# ==============================================================
# WEBSOCKET EVENT LOOP THREAD
# ==============================================================

def ws_event_loop_thread():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    ws_loop.run_forever()


# ==============================================================
# MAIN
# ==============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("  RYVA — Main Loop (g-7)")
    print("  Face + Serial + CLS + WebSocket")
    print("  Press 'q' in camera window to quit")
    print("=" * 65)
    print()
    print("  NOTE: Run ws_server.py separately first:")
    print("  uvicorn ws_server:app --host 0.0.0.0 --port 8765")
    print()
    print("-" * 65)

    t_ws = threading.Thread(target=ws_event_loop_thread, daemon=True)
    t_ws.start()
    time.sleep(0.5)

    t1 = threading.Thread(target=vision_thread,    daemon=True)
    t2 = threading.Thread(target=biosignal_thread, daemon=True)
    t3 = threading.Thread(target=cls_thread,       daemon=True)

    t1.start()
    t2.start()
    t3.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Main] Stopping RYVA...")
        stop_event.set()

    t1.join(timeout=3)
    t2.join(timeout=3)
    t3.join(timeout=3)

    print("\n[Main] RYVA stopped cleanly. ✅")
