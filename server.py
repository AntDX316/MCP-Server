from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server", description="ModelContextProtocol Server with Web UI")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_info[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat()
        }
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_info:
            del self.client_info[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    def get_active_clients(self) -> List[dict]:
        return [
            {"client_id": client_id, **info}
            for client_id, info in self.client_info.items()
        ]

manager = ConnectionManager()

# WebSocket endpoint for MCP connections
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle different message types here
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    manager.client_info[client_id]["last_ping"] = datetime.utcnow().isoformat()
                else:
                    # Echo back the message for now
                    await websocket.send_text(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from client {client_id}")
                await websocket.send_json({"error": "Invalid JSON format"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        manager.disconnect(client_id)

# REST API endpoints for configuration
class ConfigurationUpdate(BaseModel):
    setting_name: str
    value: str

@app.get("/api/clients")
async def get_clients():
    """Get list of connected clients"""
    return manager.get_active_clients()

@app.get("/api/status")
async def get_status():
    """Get server status"""
    return {
        "status": "running",
        "active_clients": len(manager.active_connections),
        "uptime": "placeholder",  # TODO: Implement uptime tracking
        "version": "1.0.0"
    }

# Serve static files (will be used for the React frontend)
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 