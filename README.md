# RYVA
### Edge AI fatigue detection for heavy machine operators —
### catch cognitive overload before it becomes an incident.

![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/react-18-61DAFB?style=flat-square&logo=react)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Competition](https://img.shields.io/badge/Tata%20InnoVent-2026-orange?style=flat-square)

> Built for **Tata InnoVent 2026**

---

## The Problem

Fatigue-related incidents in heavy machinery operations — excavators, cranes, hydraulic lifts — kill and injure thousands of workers every year. Current systems react *after* a lapse. Warning lights fire after the operator has already nodded off. Supervisors have no visibility until something breaks.

**RYVA changes the timing.** It detects cognitive overload *while the operator is still functioning* — with enough lead time for a supervisor to intervene, a rest break to be scheduled, or an alert to redirect attention before metal moves in the wrong direction.

---

## How It Works

```
Webcam ──► Face Pipeline ──► CLS Engine ──► WebSocket Server
              (EAR, pitch,       (0–100         │
               gaze, blink)       score)         ▼
                                          Supervisor Dashboard
Arduino ──► Serial Receiver ──►               +
  (MPU6050,    (motion, temp,        Operator HMI (PyQt6)
   DHT22,       vibration)           + Voice Alerts
   Buzzer)                           + Physical Buzzer
```

RYVA fuses two signal streams — facial fatigue indicators from a webcam and wrist biosignals from an Arduino wristband — into a single **Cognitive Load Score (CLS)**. The score drives a three-state alert system: GREEN (safe), AMBER (watch), RED (intervene now). Every component runs locally. No cloud. No latency penalty. No data leaving the site.

---

## Key Features

- **Dual-signal CLS fusion** — eye closure (EAR), head pitch, blink rate, and gaze combined with wrist acceleration variance, temperature, and vibration into one score
- **Hysteresis-controlled state transitions** — 10s to upgrade, 60s to downgrade; eliminates alert flickering under momentary signal noise
- **Live supervisor dashboard** — React + WebSocket UI with per-operator gauges, event log, PPE violation tracker, incident report modal with 5-minute CLS history chart, and RED arrival time prediction
- **PPE detection** — YOLOv8-nano fine-tuned on 8,099 images; **89.8% mAP@50 for hard hat detection**
- **Bilingual voice alerts** — Tamil and English audio warnings generated locally via gTTS + pygame; no internet required
- **Physical wristband alert** — onboard buzzer fires independently of the software pipeline for zero-latency local feedback
- **Operator calibration** — 3-minute baseline capture personalises the CLS formula per operator per shift
- **Edge-first architecture** — all inference runs on-device; no cloud API, no external dependency at runtime
- **Simulation mode** — WebSocket server ships with a built-in CLS simulator for dashboard-only demos

---

## Tech Stack

| Layer | Technology |
|---|---|
| Supervisor Dashboard | React 18, TypeScript, Vite, Recharts |
| WebSocket Server | FastAPI, uvicorn[standard] |
| Face Pipeline | OpenCV, MediaPipe 0.10.13 |
| CLS Engine | Python 3.12, NumPy, SciPy |
| PPE Detection | YOLOv8-nano (Ultralytics), SH17 dataset |
| Operator HMI | PyQt6, pygame, gTTS |
| Biosignal Receiver | PySerial (USB Serial from Arduino) |
| Hardware | Arduino Uno, MPU6050, DHT22, Piezo Buzzer |

---

## Prerequisites

- Python 3.12 *(3.13+ not recommended — prebuilt wheels missing for mediapipe and pygame)*
- Node.js 18+
- Arduino IDE
- A webcam (720p minimum)
- Arduino Uno wired per `docs/wiring.md`

---

## Installation

**Clone the repository**

```bash
git clone https://github.com/Nivashini-oracle/ryva.git
cd ryva
```

**Create a Python 3.12 virtual environment**

```bash
py -3.12 -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

**Install Python dependencies**

```bash
pip install fastapi "uvicorn[standard]" opencv-python \
    mediapipe==0.10.13 websocket-client websockets \
    pygame PyQt6 pyserial requests numpy scipy \
    ultralytics torch torchvision
```

**Install dashboard dependencies**

```bash
cd dashboard
npm install
cd ..
```

**Upload Arduino firmware**

1. Open `firmware/ryva_wristband.ino` in Arduino IDE
2. Set board to **Arduino Uno**, select the correct COM port
3. Upload — verify Serial Monitor shows:

```
MPU6050 OK
MPU:0.740,0.681,0.040|TEMP:35.9|HUM:63.6|VAR:0.0001|VIB:0
```

---

## Running RYVA

Open four terminals. Activate the venv in each.

**Terminal 1 — WebSocket server**

```bash
uvicorn wss_server:app --host 0.0.0.0 --port 8765
```

**Terminal 2 — Sensing and scoring pipeline**

```bash
python main_loop.py
```

Auto-detects the Arduino COM port. Opens the webcam. Starts broadcasting CLS updates to the server every second.

**Terminal 3 — Supervisor dashboard**

```bash
cd dashboard
npm run dev
```

Open `http://localhost:5173`.

**Terminal 4 — Operator HMI**

```bash
python ryva_hmi.py
```

Shows the calibration countdown, then switches to the live GREEN / AMBER / RED operator view. Voice alerts fire automatically on state transitions.

**Dashboard-only demo (no hardware required)**

The WebSocket server includes a built-in CLS simulator. Run Terminal 1 and Terminal 3 only — the dashboard animates with simulated operator data immediately.

---

## Project Structure

```
ryva/
├── vision/
│   ├── face_pipeline.py          # EAR, head pose, gaze — 25fps
│   └── ppe_model/
│       └── best.pt               # YOLOv8-nano weights (89.8% mAP)
├── biosignal/
│   └── serial_receiver.py        # Arduino USB serial reader
├── cognitive_engine/
│   └── cls_engine.py             # Rule-based CLS formula
├── hmi/
│   └── ryva_hmi.py               # PyQt6 HMI + voice alerts
├── dashboard/
│   └── src/
│       ├── App.tsx
│       ├── types.ts
│       └── components/
│           ├── MachineGrid.tsx   # Per-operator gauge cards
│           ├── EventPanel.tsx    # Live event log
│           ├── StatCards.tsx     # Shift summary stats
│           ├── Sidebar.tsx       # Operator list + system status
│           └── IncidentReport.tsx
├── firmware/
│   └── ryva_wristband.ino        # Arduino firmware
├── audio/                        # Pre-generated voice alert MP3s
├── docs/
│   ├── wiring.md
│   └── training_results/         # PPE model curves and metrics
├── wss_server.py                 # FastAPI WebSocket relay server
├── main_loop.py                  # Central inference loop
└── data_direct.yaml              # PPE training dataset config
```

---

## CLS Reference

| Score | State | Meaning |
|---|---|---|
| 0 – 40 | GREEN | Operator alert — normal |
| 41 – 70 | AMBER | Fatigue accumulating — notify supervisor |
| 71 – 100 | RED | Cognitive overload — intervene now |

Upgrade: 10 seconds sustained above threshold.
Downgrade: 60 seconds sustained below (15 seconds in demo mode).

---

## PPE Model Performance

Trained on the SH17 dataset (8,099 images, Tesla T4 GPU, 30 epochs, ~54 minutes).

| Class | mAP@50 |
|---|---|
| Hard Hat | **89.8%** |
| Earplugs | 86.1% |
| Welding Helmet | 77.8% |
| Safety Vest | 59.1% |
| Overall (17 classes) | 51.6% |

---

## Contributing

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feat/your-feature-name
```

3. Commit with a clear message

```bash
git commit -m "feat: description of what you built"
```

4. Push and open a Pull Request against `main`

```bash
git push origin feat/your-feature-name
```

Open an issue first for significant changes.

---

## Team

Built for **Tata InnoVent 2026** by a 4-person team from SASTRA Deemed University, Thanjavur.

**Grismitha** — Supervisor dashboard (React + TypeScript), WebSocket server, real-time CLS visualisation, PPE model training (YOLOv8-nano), PPE violation UI, incident report panel, system integration

**Nivashini** — Face pipeline (MediaPipe), CLS engine, main inference loop, serial biosignal receiver, fatigue trajectory prediction

**Ishaa** — Arduino firmware, sensor wiring (MPU6050, DHT22, Buzzer), wristband hardware assembly

**Miruthini** — Operator HMI (PyQt6), voice alert generation (gTTS), calibration screen

---

## License

MIT License — see [LICENSE](./LICENSE) for full terms.

---

*RYVA — because the seconds before an incident are the only ones that matter.*
