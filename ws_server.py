import asyncio
import json
import random
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

        current_state = get_state(sim_cls)
        ts = datetime.now().strftime("%H:%M:%S")

        await manager.broadcast({
            "type": "cls_update",
            "operator_id": "R001",
            "cls": round(sim_cls, 1),
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
    return {"status": "ok", "clients": len(manager.active_connections)}

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

