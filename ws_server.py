# ws_server.py
import asyncio
import json
import random
import time
from datetime import datetime
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Enable CORS for the React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return
        
        data = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.add(connection)
        
        # Clean up dead connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep connection alive and listen for any messages from client
        while True:
            # Wait for any client message (ping/pong)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        manager.disconnect(websocket)

# Optional: Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "clients": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# Simulate CLS data (for testing without actual sensors)
async def simulate_data():
    """Generate fake CLS data for testing the dashboard"""
    import random
    
    # Start with healthy values
    cls = 25
    state = "GREEN"
    operator_id = "R001"
    
    # Event types to simulate
    event_types = ["AMBER", "RED", "PPE VIOLATION", "SOS"]
    event_probs = [0.05, 0.02, 0.03, 0.01]  # Probability per second
    
    # PPE violation tracking
    ppe_violation_active = False
    ppe_timer = 0
    
    while True:
        # Simulate gradual fatigue build-up (CLS fluctuates)
        # Random walk with slight upward drift
        change = random.uniform(-2, 3)
        cls = max(10, min(95, cls + change))
        
        # Determine state based on CLS
        if cls >= 71:
            state = "RED"
        elif cls >= 41:
            state = "AMBER"
        else:
            state = "GREEN"
        
        # 1. Send CLS update every second
        cls_msg = {
            "type": "cls_update",
            "operator_id": operator_id,
            "cls": round(cls, 1),
            "state": state
        }
        await manager.broadcast(cls_msg)
        
        # 2. Randomly trigger events
        if random.random() < event_probs[0] and state in ["AMBER", "RED"]:
            # AMBER event
            event_msg = {
                "type": "event",
                "event_type": "AMBER",
                "operator_id": operator_id,
                "ts": datetime.now().strftime("%H:%M:%S")
            }
            await manager.broadcast(event_msg)
        
        if random.random() < event_probs[1] and state == "RED":
            # RED event - also trigger incident report
            event_msg = {
                "type": "event",
                "event_type": "RED",
                "operator_id": operator_id,
                "ts": datetime.now().strftime("%H:%M:%S")
            }
            await manager.broadcast(event_msg)
            
            # Incident report
            incident_msg = {
                "type": "incident_report",
                "data": {
                    "operator_id": operator_id,
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "cls_history": [
                        {"t": i * 30, "cls": random.randint(40, 85)} 
                        for i in range(10)
                    ],
                    "recommendation": "Schedule immediate rest break. Operator has been in RED zone for 3+ minutes."
                }
            }
            await manager.broadcast(incident_msg)
        
        # 3. Simulate PPE violation (toggle every 15-30 seconds)
        ppe_timer += 1
        if ppe_timer > random.randint(15, 30):
            ppe_timer = 0
            ppe_violation_active = not ppe_violation_active
            
            if ppe_violation_active:
                # PPE violation triggered
                missing = random.sample(["helmet", "vest"], k=random.randint(1, 2))
                ppe_msg = {
                    "type": "ppe_violation",
                    "operator_id": operator_id,
                    "missing": missing,
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "cleared": False
                }
                await manager.broadcast(ppe_msg)
            else:
                # PPE violation cleared
                ppe_msg = {
                    "type": "ppe_violation",
                    "operator_id": operator_id,
                    "missing": [],
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "cleared": True
                }
                await manager.broadcast(ppe_msg)
        
        # 4. Send CLS history for trajectory prediction (every 60s)
        if random.random() < 0.02:  # ~2% chance per second = ~once per minute
            history_msg = {
                "type": "cls_history",
                "operator_id": operator_id,
                "data": [
                    {"t": i * 10, "cls": random.randint(30, 70)} 
                    for i in range(60)  # 10 minute history
                ]
            }
            await manager.broadcast(history_msg)
        
        await asyncio.sleep(1)

# Start the server with data simulation
@app.on_event("startup")
async def startup_event():
    # Run the simulation in the background
    asyncio.create_task(simulate_data())
    print("🚀 WebSocket server started with data simulation")
    print("📡 Broadcasting to: ws://localhost:8765/ws")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )