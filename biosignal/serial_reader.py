import serial
import re
import time

PORT = "COM5"  # <-- change to your Uno full port (Arduino IDE > Tools > Port)
BAUD = 9600

PATTERN = re.compile(
    r"MPU:([-\d.]+),([-\d.]+),([-\d.]+)\|TEMP:([-\d.]+)\|HUM:([-\d.]+)\|VAR:([-\d.]+)\|VIB:([01])"
)


def read_wristband():
    """Generator that yields parsed sensor readings from the Uno over serial."""
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # let the Uno reset after the serial port opens
    while True:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
        except Exception:
            continue
        match = PATTERN.match(line)
        if match:
            ax, ay, az, temp, hum, var, vib = match.groups()
            yield {
                "ax": float(ax),
                "ay": float(ay),
                "az": float(az),
                "temp": float(temp),
                "hum": float(hum),
                "variance": float(var),
                "vibration": bool(int(vib)),
            }


if __name__ == "__main__":
    for reading in read_wristband():
        print(reading)

