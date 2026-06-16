# RYVA Dashboard

Supervisor dashboard for the RYVA cognitive load safety system.

## What it does

Displays real-time cognitive fatigue scores for machine operators on a factory floor. The supervisor watches this screen and can intervene before an operator becomes dangerously fatigued.

Each machine card shows:
- A circular gauge with the operator's CLS (Cognitive Load Score) from 0 to 100
- A coloured state dot — green (alert), amber (fatigued), red (danger)
- The operator's machine ID

## Tech Stack

- React + TypeScript (Vite)
- Recharts (RadialBarChart for the gauge)

## State thresholds

| Score | State | Meaning |
|-------|-------|---------|
| 0 – 40 | 🟢 GREEN | Operator is alert |
| 41 – 70 | 🟡 AMBER | Fatigue building |
| 71 – 100 | 🔴 RED | High risk — intervene |

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:5173`

## Current status

Week 1 — static UI with hardcoded data. WebSocket integration with the Python inference server comes in Week 2.

## Part of

RYVA — Real-time operator safety system  
Tata InnoVent 2026
