import os
import json

# Patch for Pydantic v2 compatibility with existing k8s env vars
origins = os.environ.get("ALLOWED_ORIGINS", "")
if origins and not origins.startswith("["):
    os.environ["ALLOWED_ORIGINS"] = json.dumps([o.strip() for o in origins.split(",")])

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time

# Import AgentRegistry from the existing source
try:
    from twisterlab.agents.registry import AgentRegistry
except ImportError:
    import sys
    sys.path.append(os.path.join(os.getcwd(), "src"))
    from twisterlab.agents.registry import AgentRegistry

app = FastAPI(title="TwisterLab Mission Control API", version="4.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class AgentToggleRequest(BaseModel):
    agent_id: str
    active: bool

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/api/v1/agents/")
async def list_agents():
    registry = AgentRegistry()
    if not registry._initialized:
        registry.discover()
        
    agents = []
    # Use _agents which is the correct internal dict for v4.0 registry
    for agent_id, info in registry._agents.items():
        instance = info.get("instance")
        agents.append({
            "id": agent_id,
            "name": agent_id.replace("_", " ").title(),
            "status": "online" if instance else "standby",
            "load": "12%" if instance else "0%",
            "uptime": "2h 45m" if instance else "0s",
            "type": "autonomous" if "maestro" in agent_id else "utility"
        })
    return agents

@app.post("/api/v1/agents/toggle")
async def toggle_agent(req: AgentToggleRequest):
    registry = AgentRegistry()
    try:
        if req.active:
            # Initialize agent if not already active
            registry.get_agent(req.agent_id)
            status = "online"
        else:
            # Shutdown/Remove instance
            info = registry._agents.get(req.agent_id)
            if info:
                info["instance"] = None
            status = "standby"
        
        # Broadcast the change
        await manager.broadcast({
            "type": "AGENT_STATUS_UPDATE",
            "agent_id": req.agent_id,
            "status": status
        })
        return {"status": "success", "agent_id": req.agent_id, "new_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/maestro/task")
async def orchestrate_task(payload: dict):
    task_id = f"task_{int(time.time())}"
    return {"status": "accepted", "task_id": task_id}

@app.websocket("/ws/telemetry")
async def telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            registry = AgentRegistry()
            if not registry._initialized:
                registry.discover()
            
            active_count = sum(1 for a in registry._agents.values() if a.get("instance"))
            total_count = len(registry._agents)
            
            await websocket.send_json({
                "type": "TELEMETRY_UPDATE",
                "cpu": 24,
                "ram": 42,
                "agents": total_count,
                "active_agents": active_count,
                "socialEvents": [
                    {"id": 1, "user": "System", "action": "Fleet Registry Synchronized", "sentiment": "NEUTRAL"}
                ]
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
