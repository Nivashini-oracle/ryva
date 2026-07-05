# =============================================================
# RYVA Project — main_loop.py  (updated g-9)
# Purpose : Links face pipeline + serial receiver + CLS engine
#           Sends CLS updates to the dashboard/HMI over a real
#           WebSocket CLIENT connection to wss_server.py
# Author  : RYVA Team
# Usage   : python main_loop.py
# NOTE    : Start wss_server.py FIRST (uvicorn wss_server:app --host 0.0.0.0 --port 8765)
# Done When:
#   Dashboard gauge updates every second from real Arduino data
#   Move wrist quickly → movement_var rises → CLS rises
#
# FIX (g-9): main_loop.py previously did `from wss_server import
# broadcast`, which — since main_loop.py and wss_server.py run as
# separate OS processes — created its own empty in-memory copy of
# wss_server's `clients` set instead of reaching the real running
# server. broadcast() ran with zero connected clients, silently.
# Fixed by making main_loop.py a real WebSocket CLIENT that connects
# to ws://localhost:8765/ws over the network, same pattern already
# used successfully in ryva_hmi.py.
# =============================================================

import cv2
import time
import json
import queue
import threading
import collections
import sys
import os

import websocket  # pip install websocket-client

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision.face_pipeline              import FacePipeline
from cognitive_engine.cls_engine       import compute_cls, get_cls_band, DEFAULT_BASELINE
from biosignal.serial_receiver         import serial_receiver

# ==============================================================
# CONFIGURATION
# ==============================================================

CLS_INTERVAL            = 1.0
WINDOW_SIZE              = 25
CALIBRATION_SECONDS      = 10   # keep in sync with ryva_hmi.py's CALIBRATION_SECONDS
MOVE_MAX_SAFETY_MARGIN   = 1.3  # personal move_max = observed max * this margin
WS_URL                   = "ws://localhost:8765/ws"

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

# ==============================================================
# WEBSOCKET CLIENT — real network connection to wss_server.py
# ==============================================================

_ws_client = None
_ws_lock   = threading.Lock()


def ws_client_thread():
    """
    Keeps a persistent WebSocket CLIENT connection open to the real
    running wss_server.py process. Reconnects automatically if the
    connection drops.

    IMPORTANT: wss_server.py's broadcast() sends every payload to ALL
    connected clients - and main_loop.py IS a client (it connects to
    send). So the server echoes our own data straight back to us every
    second. If nothing ever reads that incoming data, it piles up in
    the socket's receive buffer until Windows aborts the connection
    (WinError 10053). So this loop actively calls .recv() to drain and
    discard whatever comes back, instead of idling or pinging.
    """
    global _ws_client
    while not stop_event.is_set():
        try:
            with _ws_lock:
                _ws_client = websocket.create_connection(WS_URL, timeout=2)
            print(f"[WS] main_loop connected to {WS_URL}")

            while not stop_event.is_set():
                try:
                    # Drain the server's broadcast echo. timeout=2 means
                    # this returns every ~2s even with no data, so the
                    # stop_event check above still runs regularly.
                    _ws_client.recv()
                except websocket._exceptions.WebSocketTimeoutException:
                    continue

        except Exception as e:
            print(f"[WS] Connection lost/failed ({e}) - retrying in 2s...")
            with _ws_lock:
                _ws_client = None
            time.sleep(2)


def ws_send(payload: dict):
    """Send a payload to wss_server.py over the real WebSocket connection."""
    with _ws_lock:
        if _ws_client is None:
            return
        try:
            _ws_client.send(json.dumps(payload))
        except Exception as e:
            print(f"[WS] Send failed: {e}")


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

    # ----------------------------------------------------------
    # CALIBRATION PHASE — build a real personal baseline
    # ----------------------------------------------------------
    print(f"[CLS] Calibrating — collecting baseline for {CALIBRATION_SECONDS}s. "
          f"Look at the camera and hold the wristband normally...")

    calib_ear_samples  = []
    calib_move_samples = []
    calib_start = time.time()

    while not stop_event.is_set() and (time.time() - calib_start) < CALIBRATION_SECONDS:
        with face_lock:
            calib_ear_samples.append(latest_face["ear"])
        with serial_lock:
            calib_move_samples.append(serial_state["movement_var"])
        time.sleep(0.2)

    if calib_ear_samples:
        personal_ear = sum(calib_ear_samples) / len(calib_ear_samples)
    else:
        personal_ear = DEFAULT_BASELINE["ear"]

    if calib_move_samples:
        personal_move_max = max(calib_move_samples) * MOVE_MAX_SAFETY_MARGIN
        personal_move_max = max(personal_move_max, DEFAULT_BASELINE["move_max"] * 0.3)
    else:
        personal_move_max = DEFAULT_BASELINE["move_max"]

    baseline = {
        "ear"      : round(personal_ear, 3),
        "move_max" : round(personal_move_max, 2),
    }

    print(f"[CLS] Calibration done ✅ — personal baseline: "
          f"ear={baseline['ear']}, move_max={baseline['move_max']} "
          f"(from {len(calib_ear_samples)} samples)")

    # ----------------------------------------------------------
    # MAIN LOOP
    # ----------------------------------------------------------
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
            baseline     = baseline
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

        payload = {
            "type"         : "cls_update",
            "operator_id"  : "R001",
            "cls"          : score,
            "state"        : band,
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

        ws_send(payload)

        elapsed    = time.time() - loop_start
        time.sleep(max(0, CLS_INTERVAL - elapsed))

    print("[CLS] Thread stopped.")


# ==============================================================
# MAIN
# ==============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("  RYVA — Main Loop (g-9)")
    print("  Face + Serial + CLS + WebSocket client")
    print("  Press 'q' in camera window to quit")
    print("=" * 65)
    print()
    print("  NOTE: Run wss_server.py separately first:")
    print("  uvicorn wss_server:app --host 0.0.0.0 --port 8765")
    print()
    print("-" * 65)

    t_ws = threading.Thread(target=ws_client_thread, daemon=True)
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