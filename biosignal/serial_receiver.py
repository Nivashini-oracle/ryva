# =============================================================
# RYVA Project — biosignal/serial_receiver.py
# Purpose : Reads Arduino USB serial data via PySerial
#           Replaces original BLE receiver (bleak library)
# Author  : RYVA Team
# Usage   : python biosignal/serial_receiver.py
# Arduino sends every second:
#   MPU:ax,ay,az|TEMP:t|HUM:h|VAR:v|VIB:0or1
# Done When:
#   Terminal prints movement_var, temp, hum, vib every second
#   Unplug Arduino → disconnect message appears
#   Replug Arduino → auto-reconnects within 5 seconds
# =============================================================

import serial
import serial.tools.list_ports
import time
import queue
import threading

# ==============================================================
# CONFIGURATION
# ==============================================================

BAUD_RATE      = 9600    # Must match Arduino Serial.begin(9600)
TIMEOUT        = 2       # Serial read timeout in seconds
RETRY_INTERVAL = 3       # Seconds to wait before reconnect attempt


# ==============================================================
# STEP 1 — FIND ARDUINO PORT
# Scans all COM ports and returns the one with Arduino connected
# ==============================================================

def find_arduino_port():
    """
    Scans all available COM ports and finds the Arduino.
    Looks for: 'Arduino', 'CH340' (cheap Arduino clone chip),
               'USB Serial' (generic USB-Serial adapter)
    Returns:
        port name (str) e.g. 'COM3' on Windows, '/dev/ttyUSB0' on Linux
        or None if not found
    """
    ports = serial.tools.list_ports.comports()

    for p in ports:
        desc = p.description or ""
        if any(keyword in desc for keyword in
               ['Arduino', 'CH340', 'USB Serial', 'USB-SERIAL', 'ttyUSB']):
            print(f"[Serial] Found Arduino on port: {p.device} ({desc})")
            return p.device

    return None


# ==============================================================
# STEP 2 — PARSE ONE LINE FROM ARDUINO
# Input  : "MPU:0.12,0.08,9.81|TEMP:32.5|HUM:68.2|VAR:0.043|VIB:0"
# Output : dict with movement_var, temp, hum, vib
# ==============================================================

def parse_line(line):
    """
    Parses one line of Arduino serial output.

    Arduino format:
        MPU:ax,ay,az|TEMP:t|HUM:h|VAR:v|VIB:0or1

    Example:
        MPU:0.12,0.08,9.81|TEMP:32.5|HUM:68.2|VAR:0.043|VIB:0

    Returns:
        dict with keys:
            movement_var (float) : variance of movement from MPU6050
            temp         (float) : cabin temperature from DHT11 in °C
            hum          (float) : cabin humidity from DHT11 in %
            vib          (bool)  : True if vibration detected
        or None if line is malformed
    """
    try:
        # Split into key:value pairs  →  {'MPU': '0.12,0.08,9.81', 'TEMP': '32.5', ...}
        parts = dict(p.split(':', 1) for p in line.split('|'))

        # Parse MPU accelerometer values (not used in CLS yet but stored)
        ax, ay, az = map(float, parts['MPU'].split(','))

        return {
            'movement_var' : float(parts['VAR']),
            'temp'         : float(parts['TEMP']),
            'hum'          : float(parts['HUM']),
            'vib'          : parts['VIB'].strip() == '1',
            'ax'           : ax,
            'ay'           : ay,
            'az'           : az,
        }

    except Exception as e:
        # Silently skip malformed lines
        return None


# ==============================================================
# STEP 3 — SERIAL RECEIVER FUNCTION
# Runs in its own thread — auto-reconnects if Arduino unplugged
# ==============================================================

def serial_receiver(data_queue, stop_event=None):
    """
    Continuously reads from Arduino over USB serial.
    Writes parsed data dicts to data_queue every second.
    Auto-reconnects if Arduino is unplugged and replugged.

    Args:
        data_queue  : queue.Queue — shared with CLS engine thread
        stop_event  : threading.Event — set this to stop the thread
    """
    if stop_event is None:
        stop_event = threading.Event()

    print("[Serial] Receiver started — looking for Arduino...")

    while not stop_event.is_set():

        # --- Find Arduino port ---
        port = find_arduino_port()

        if not port:
            print(f"[Serial] Arduino not found. Retrying in {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)
            continue

        # --- Try to open serial connection ---
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=TIMEOUT)
            print(f"[Serial] ✅ Connected to Arduino on {port} at {BAUD_RATE} baud")
            time.sleep(2)  # Let Arduino reset after serial connect

            while not stop_event.is_set():
                # Read one line from Arduino
                raw = ser.readline()

                if not raw:
                    print("[Serial] ⚠️  No data received — Arduino may be disconnected.")
                    break

                line = raw.decode('utf-8', errors='ignore').strip()

                if not line:
                    continue

                # Parse the line
                parsed = parse_line(line)

                if parsed:
                    # Put into shared queue (drop oldest if full)
                    if data_queue.full():
                        try:
                            data_queue.get_nowait()
                        except queue.Empty:
                            pass
                    data_queue.put(parsed)

                else:
                    print(f"[Serial] Could not parse line: {line}")

        except serial.SerialException as e:
            print(f"[Serial] ❌ Serial error: {e}")
            print(f"[Serial] Reconnecting in {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)

        except Exception as e:
            print(f"[Serial] Unexpected error: {e}")
            print(f"[Serial] Reconnecting in {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)

    print("[Serial] Receiver stopped.")


# ==============================================================
# QUICK TEST — Run this file directly
# python biosignal/serial_receiver.py
# Press Ctrl+C to quit
# ==============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  RYVA — Serial Receiver Test")
    print("  Plug in Arduino and watch data print every second")
    print("  Press Ctrl+C to quit")
    print("=" * 60)
    print()

    # Create shared queue
    data_queue = queue.Queue(maxsize=10)
    stop_event = threading.Event()

    # Start serial receiver in background thread
    t = threading.Thread(
        target=serial_receiver,
        args=(data_queue, stop_event),
        name="SerialReceiverThread",
        daemon=True
    )
    t.start()

    print(f"\n  {'movement_var':<15} {'temp':<8} {'hum':<8} {'vib':<6} {'ax':<8} {'ay':<8} az")
    print("-" * 65)

    try:
        while True:
            try:
                # Wait up to 5 seconds for data
                data = data_queue.get(timeout=5)

                print(
                    f"  {data['movement_var']:<15.4f} "
                    f"{data['temp']:<8.1f} "
                    f"{data['hum']:<8.1f} "
                    f"{str(data['vib']):<6} "
                    f"{data['ax']:<8.3f} "
                    f"{data['ay']:<8.3f} "
                    f"{data['az']:.3f}"
                )

            except queue.Empty:
                print("  [Waiting for Arduino data...]")

    except KeyboardInterrupt:
        print("\n\n[Main] Ctrl+C received — stopping...")
        stop_event.set()

    t.join(timeout=3)
    print("[Main] Serial receiver stopped cleanly. ✅")
