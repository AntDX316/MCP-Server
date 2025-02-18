from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from collections import deque
import database as db
import config as cfg
import services

# Load configuration
config = cfg.Config()

# Configure logging based on debug mode
logging.basicConfig(
    level=logging.DEBUG if config.server.debug else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server", description="ModelContextProtocol Server with Web UI")

# CORS middleware configuration with explicit methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, dict] = {}
        self.start_time = datetime.now(timezone.utc)
        self.update_task = None

    async def start_history_tracking(self):
        """Start the connection history tracking task"""
        self.update_task = asyncio.create_task(self._update_connection_history())

    async def _update_connection_history(self):
        """Background task to update connection history"""
        while True:
            current_connections = len(self.active_connections)
            current_time = datetime.now(timezone.utc)
            # Store in database with current time
            db.add_connection_record(current_connections, current_time)
            # Clean up old records
            db.cleanup_old_records()
            await asyncio.sleep(10)  # Update every 10 seconds instead of every minute

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_info[client_id] = {
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_ping": datetime.now(timezone.utc).isoformat()
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

    def get_connection_history(self) -> List[dict]:
        # Get history from database
        history = db.get_connection_history()
        
        # Return the raw data without aggregation
        return [
            {
                "time": entry["timestamp"],
                "connections": int(entry["connections"])  # Ensure integer values
            }
            for entry in history
        ]

    def get_uptime(self) -> str:
        uptime = datetime.now(timezone.utc) - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts"""
    await manager.start_history_tracking()

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
                    manager.client_info[client_id]["last_ping"] = datetime.now(timezone.utc).isoformat()
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
class ServerSettingsUpdate(BaseModel):
    host: str
    port: int
    debug: bool
    max_connections: int
    ping_timeout: int
    ssl_enabled: bool
    ssl_cert_path: Optional[str]
    ssl_key_path: Optional[str]

class MCPSettingsUpdate(BaseModel):
    protocol_version: str
    max_context_length: int
    default_temperature: float
    max_tokens: int

class SettingsUpdate(BaseModel):
    server: ServerSettingsUpdate
    mcp: MCPSettingsUpdate

@app.get("/api/settings")
async def get_settings():
    """Get current server and MCP settings"""
    try:
        # Convert Pydantic models to dictionaries for JSON serialization
        server_config = {
            "host": config.server.host,
            "port": config.server.port,
            "debug": config.server.debug,
            "max_connections": config.server.max_connections,
            "ping_timeout": config.server.ping_timeout,
            "ssl_enabled": config.server.ssl_enabled,
            "ssl_cert_path": config.server.ssl_cert_path or "",
            "ssl_key_path": config.server.ssl_key_path or ""
        }
        
        mcp_config = {
            "protocol_version": config.mcp.protocol_version,
            "max_context_length": config.mcp.max_context_length,
            "default_temperature": config.mcp.default_temperature,
            "max_tokens": config.mcp.max_tokens
        }
        
        return {
            "server": server_config,
            "mcp": mcp_config
        }
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update server and MCP settings"""
    try:
        # Update server settings
        config.update_server_config(settings.server.dict())
        
        # Update MCP settings
        config.update_mcp_config(settings.mcp.dict())
        
        logger.info("Settings updated successfully")
        return {"status": "success", "message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients")
async def get_clients():
    """Get list of connected clients"""
    return manager.get_active_clients()

@app.get("/api/status")
async def get_status(hours: float = 1):
    """Get server status"""
    history = db.get_connection_history(hours=hours)
    # Ensure timestamps are in ISO format with timezone
    for entry in history:
        if isinstance(entry["timestamp"], datetime):
            entry["time"] = entry["timestamp"].isoformat()
        else:
            entry["time"] = entry["timestamp"]
        del entry["timestamp"]

    return {
        "status": "running",
        "active_clients": len(manager.active_connections),
        "uptime": manager.get_uptime(),
        "version": "1.0.0",
        "connection_history": history
    }

@app.delete("/api/clients/{client_id}")
async def disconnect_client(client_id: str):
    """Disconnect a specific client"""
    if client_id not in manager.active_connections:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        # Close the WebSocket connection
        await manager.active_connections[client_id].close()
        # Remove from manager
        manager.disconnect(client_id)
        return {"status": "success", "message": f"Client {client_id} disconnected"}
    except Exception as e:
        logger.error(f"Error disconnecting client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Define the service config update model
class ServiceConfigUpdate(BaseModel):
    enabled: bool
    config: Optional[Dict[str, str]] = None

@app.get("/api/services")
async def get_services():
    """Get all services configuration"""
    return services.services_manager.get_all_services()

@app.get("/api/services/{service_id}")
async def get_service(service_id: str):
    """Get configuration for a specific service"""
    service_config = services.services_manager.get_service_config(service_id)
    if service_config is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service_config

@app.put("/api/services/{service_id}")
async def update_service(service_id: str, config_update: ServiceConfigUpdate):
    """Update configuration for a specific service"""
    try:
        logger.info(f"Updating service {service_id} - enabled: {config_update.enabled}")
        
        # Get current service config
        current_config = services.services_manager.get_service_config(service_id)
        if current_config is None:
            logger.warning(f"Service {service_id} not found")
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")

        # Update the service
        updated_config = await services.services_manager.update_service_config(
            service_id,
            enabled=config_update.enabled,
            config=config_update.config or {}
        )
        
        logger.info(f"Service {service_id} updated successfully")
        return {
            "status": "success",
            "message": f"Service {service_id} updated successfully",
            "enabled": updated_config.enabled,
            "config": updated_config.config
        }
    except ValueError as e:
        logger.error(f"Invalid configuration for service {service_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating service {service_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (will be used for the React frontend)
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {config.server.host}:{config.server.port}")
    logger.info(f"Debug mode: {'enabled' if config.server.debug else 'disabled'}")
    logger.info(f"SSL: {'enabled' if config.server.ssl_enabled else 'disabled'}")
    
    if config.server.ssl_enabled:
        if not config.server.ssl_cert_path or not config.server.ssl_key_path:
            logger.error("SSL is enabled but certificate or key path is missing!")
            exit(1)
        if not os.path.exists(config.server.ssl_cert_path):
            logger.error(f"SSL certificate file not found: {config.server.ssl_cert_path}")
            exit(1)
        if not os.path.exists(config.server.ssl_key_path):
            logger.error(f"SSL key file not found: {config.server.ssl_key_path}")
            exit(1)
            
        logger.info("Starting server with SSL enabled")
        uvicorn.run(
            "server:app",
            host=config.server.host,
            port=config.server.port,
            ssl_keyfile=config.server.ssl_key_path,
            ssl_certfile=config.server.ssl_cert_path,
            log_level="debug" if config.server.debug else "info",
            reload=config.server.debug
        )
    else:
        uvicorn.run(
            "server:app",
            host=config.server.host,
            port=config.server.port,
            log_level="debug" if config.server.debug else "info",
            reload=config.server.debug
        ) 