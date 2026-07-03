import asyncio
import json
import random
import threading
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ---- TOGGLE: flip to False to fall back to pure simulation if hardware fails ----
USE_HARDWARE = False

if USE_HARDWARE:
    from biosignal.serial_reader import read_wristband

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                dead.append(connection)
        for d in dead:
            if d in self.active_connections:
                self.active_connections.remove(d)

manager = ConnectionManager()

def get_state(cls: float) -> str:
    if cls <= 40:
        return "GREEN"
    elif cls <= 70:
        return "AMBER"
    else:
        return "RED"

# ---- shared state updated by the biosignal thread ----
latest_biosignal = {
    "ax": 0.0, "ay": 0.0, "az": 0.0,
    "temp": 0.0, "hum": 0.0,
    "variance": 0.0, "vibration": False,
}

def biosignal_thread():
    """Runs in background, continuously updates latest_biosignal from the Uno."""
    for reading in read_wristband():
        latest_biosignal.update(reading)

if USE_HARDWARE:
    threading.Thread(target=biosignal_thread, daemon=True).start()

def compute_cls(base_cls: float) -> float:
    """
    Fuse the simulated/vision base CLS with real wristband biosignal data.
    Placeholder fusion logic — adjust weighting once cognitive_engine defines
    how variance/vibration should factor in officially.
    """
    cls = base_cls
    if USE_HARDWARE:
        if latest_biosignal["vibration"]:
            cls += 7
        cls += min(latest_biosignal["variance"] * 2, 5)  # capped nudge
    return max(0, min(100, cls))

sim_cls = 30.0
sim_direction = 1

async def simulation_loop():
    global sim_cls, sim_direction
    last_state = "GREEN"

    while True:
        await asyncio.sleep(1)

        sim_cls += sim_direction * random.uniform(0.5, 2.0)
        if sim_cls >= 85:
            sim_direction = -1
        if sim_cls <= 15:
            sim_direction = 1
        sim_cls = max(0, min(100, sim_cls))

        fused_cls = compute_cls(sim_cls)
        current_state = get_state(fused_cls)
        ts = datetime.now().strftime("%H:%M:%S")

        await manager.broadcast({
            "type": "cls_update",
            "operator_id": "R001",
            "cls": round(fused_cls, 1),
            "state": current_state,
        })

        if current_state != last_state:
            await manager.broadcast({
                "type": "event",
                "event_type": current_state,
                "operator_id": "R001",
                "ts": ts,
            })
            last_state = current_state

@app.on_event("startup")
async def startup():
    asyncio.create_task(simulation_loop())

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "clients": len(manager.active_connections),
        "hardware": USE_HARDWARE,
        "latest_biosignal": latest_biosignal if USE_HARDWARE else None,
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await manager.broadcast(msg)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("ws_server:app", host="0.0.0.0", port=8765, reload=False)