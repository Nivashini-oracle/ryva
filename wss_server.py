# =============================================================
# RYVA Project — ws_server.py
# Purpose : WebSocket server — sends CLS updates to dashboard
# Author  : RYVA Team
# Usage   : uvicorn ws_server:app --host 0.0.0.0 --port 8765
# =============================================================

import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow dashboard (React) to connect from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set of all connected dashboard clients
clients: set[WebSocket] = set()


# ==============================================================
# WebSocket endpoint — dashboard connects here
# ==============================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    print(f"[WS] Dashboard connected. Total clients: {len(clients)}")
    try:
        while True:
            # Keep connection alive — wait for any message
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.discard(websocket)
        print(f"[WS] Dashboard disconnected. Total clients: {len(clients)}")


# ==============================================================
# Broadcast — called by main_loop.py to push CLS updates
# ==============================================================

async def broadcast(message: dict):
    """
    Sends CLS update to all connected dashboard clients.
    Automatically removes dead connections.
    Args:
        message (dict): data to send e.g.
            { cls_score, band, ear, pitch, temp,
              movement_var, hum, vib, blink_rate, gaze }
    """
    dead = set()
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except Exception:
            dead.add(client)

    # Clean up disconnected clients
    for client in dead:
        clients.discard(client)


# ==============================================================
# Health check endpoint
# ==============================================================

@app.get("/")
async def root():
    return {"status": "RYVA WebSocket server running",
            "clients": len(clients)}
