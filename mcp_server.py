from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import services
from datetime import datetime, timedelta
from enum import Enum
import time
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def set_debug_mode(enabled: bool):
    """Update logging level based on debug mode"""
    if enabled:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled - verbose logging activated")
    else:
        logger.setLevel(logging.INFO)
        logger.info("Debug mode disabled - returning to normal logging")

app = FastAPI(title="MCP Server for Cursor")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Store service configurations and settings
service_configs = {
    'github': {'enabled': False, 'config': {}},
    'slack': {'enabled': False, 'config': {}},
    'google_drive': {'enabled': False, 'config': {}},
    'azure': {'enabled': False, 'config': {}},
    'vscode': {'enabled': False, 'config': {}}
}

server_settings = {
    'host': '0.0.0.0',
    'port': 8765,
    'maxConnections': 100,
    'pingTimeout': 30,
    'debugMode': False,
    'sslEnabled': False
}

mcp_settings = {
    'protocolVersion': '1.0.0',
    'maxContextLength': 4096,
    'defaultTemperature': 0.7,
    'maxTokens': 2048
}

class ContentType(str, Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"

class Content(BaseModel):
    type: ContentType
    text: str
    language: Optional[str] = None
    alt: Optional[str] = None

class ToolResponse(BaseModel):
    content: List[Content]
    isError: Optional[bool] = False

# Define available tools with proper schema for Cursor
TOOLS = [
    {
        "name": "test",
        "display_name": "Test",
        "description": "A simple test tool to verify MCP is working",
        "schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo back"
                }
            },
            "required": ["message"]
        },
        "enabled": True,
        "version": "1.0"
    },
    {
        "name": "google_drive",
        "display_name": "Google Drive",
        "description": "Access and manage files in Google Drive",
        "schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["list", "upload", "create_folder", "delete"]
                },
                "folder_id": {
                    "type": "string",
                    "description": "Google Drive folder ID (optional)"
                },
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID (required for delete operation)"
                },
                "content": {
                    "type": "string",
                    "description": "File content for upload (required for upload operation)"
                },
                "filename": {
                    "type": "string",
                    "description": "Name of the file (required for upload and create_folder operations)"
                }
            },
            "required": ["operation"]
        },
        "enabled": True,
        "version": "1.0"
    }
]

class ConnectionManager:
    def __init__(self):
        self.connected_clients: Dict[str, dict] = {}
        self.connection_history: List[dict] = []
        self.start_time = time.time()

    def add_client(self, client_id: str, websocket: WebSocket, headers: dict, client_info: dict) -> None:
        self.connected_clients[client_id] = {
            "websocket": websocket,
            "status": "Connected",
            "connected_since": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat(),
            "client_info": client_info
        }
        self.add_history_entry("connect", client_id, client_info)

    def remove_client(self, client_id: str, reason: str = "Connection closed") -> None:
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
            self.add_history_entry("disconnect", client_id, {"reason": reason})

    def update_client_ping(self, client_id: str) -> None:
        if client_id in self.connected_clients:
            self.connected_clients[client_id]["last_ping"] = datetime.now().isoformat()

    def add_history_entry(self, event: str, client_id: str, extra_info: dict = None) -> None:
        current_time = datetime.now()
        self.connection_history.append({
            "time": current_time.isoformat(),
            "connections": len(self.connected_clients),
            "debug_info": {
                "event": event,
                "client_id": client_id,
                **extra_info
            } if server_settings['debugMode'] else None
        })

    def get_history(self, minutes: int = 30) -> List[dict]:
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=minutes)
        
        # Clean up old entries
        self.connection_history = [
            entry for entry in self.connection_history 
            if datetime.fromisoformat(entry["time"]) > cutoff_time
        ]
        
        # If there are no recent entries but we have active clients,
        # add a current data point
        if len(self.connection_history) == 0 and len(self.connected_clients) > 0:
            self.add_history_entry("history_backfill", "system")
        # If the last entry was more than 10 seconds ago, add a current point
        elif len(self.connection_history) > 0:
            last_entry_time = datetime.fromisoformat(self.connection_history[-1]["time"])
            if (current_time - last_entry_time).total_seconds() > 10:
                self.add_history_entry("history_update", "system")
        
        return self.connection_history

    def get_active_clients(self) -> List[dict]:
        return [
            {
                "id": client_id,
                "status": client["status"],
                "connectedSince": client["connected_since"],
                "lastPing": client["last_ping"]
            }
            for client_id, client in self.connected_clients.items()
        ]

    def get_status(self) -> dict:
        uptime = str(timedelta(seconds=int(time.time() - self.start_time)))
        return {
            "status": "Online",
            "activeClients": len(self.connected_clients),
            "uptime": uptime,
            "version": "1.0.0"
        }

    async def start_history_tracking(self):
        async def update_history():
            while True:
                try:
                    self.add_history_entry("periodic_update", "system")
                except Exception as e:
                    logger.error(f"Error updating connection history: {str(e)}")
                await asyncio.sleep(10)  # Update every 10 seconds
        
        asyncio.create_task(update_history())

# Create a global connection manager
connection_manager = ConnectionManager()

@app.get("/sse")
async def sse(request: Request):
    """SSE endpoint that sends capabilities and heartbeat messages"""
    logger.info(f"Received SSE connection from {request.client}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    async def event_generator():
        # Send initial capabilities message
        capabilities = {
            "type": "capabilities",
            "capabilities": {
                "tools": TOOLS
            }
        }
        logger.info(f"Sending capabilities: {json.dumps(capabilities, indent=2)}")
        yield {
            "event": "message",
            "data": json.dumps(capabilities)
        }
        
        # Send heartbeat every 5 seconds
        while True:
            try:
                await asyncio.sleep(5)
                heartbeat = {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.now().isoformat()})
                }
                logger.info(f"Sending heartbeat: {json.dumps(heartbeat, indent=2)}")
                yield heartbeat
            except Exception as e:
                logger.error(f"Error in event stream: {str(e)}")
                break

    return EventSourceResponse(event_generator())

@app.post("/invoke/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """Endpoint to invoke a specific tool"""
    try:
        logger.info(f"Tool invocation request for {tool_name}")
        data = await request.json()
        
        if server_settings['debugMode']:
            logger.debug(f"Tool parameters: {json.dumps(data, indent=2)}")
            logger.debug(f"Request headers: {dict(request.headers)}")
        else:
            logger.info(f"Tool parameters: {json.dumps(data, indent=2)}")
        
        # Find the requested tool
        tool = next((t for t in TOOLS if t["name"] == tool_name), None)
        if not tool:
            logger.error(f"Tool {tool_name} not found")
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

        # Handle test tool
        if tool_name == "test":
            message = data.get("arguments", {}).get("message", "No message provided")
            return ToolResponse(
                content=[
                    Content(
                        type=ContentType.TEXT,
                        text=f"Test successful! Message: {message}"
                    )
                ]
            )

        # Handle Google Drive tool
        if tool_name == "google_drive":
            # Map the operation to the appropriate handler method
            operation = data.get("arguments", {}).get("operation")
            if not operation:
                raise ValueError("Operation not specified")

            handler = services.services_manager.get_handler("google_drive")
            if not handler:
                raise ValueError("Google Drive service not initialized")

            # Execute the operation
            result = None
            if operation == "list":
                result = await handler.list_files(
                    folder_id=data.get("arguments", {}).get("folder_id"),
                    page_size=10
                )
            elif operation == "upload":
                content = data.get("arguments", {}).get("content")
                filename = data.get("arguments", {}).get("filename")
                if not content or not filename:
                    raise ValueError("Content and filename required for upload")
                result = await handler.upload_file(
                    file_content=content.encode(),
                    filename=filename,
                    mime_type="text/plain",
                    folder_id=data.get("arguments", {}).get("folder_id")
                )
            elif operation == "create_folder":
                folder_name = data.get("arguments", {}).get("filename")
                if not folder_name:
                    raise ValueError("Folder name required")
                result = await handler.create_folder(
                    folder_name=folder_name,
                    parent_folder_id=data.get("arguments", {}).get("folder_id")
                )
            elif operation == "delete":
                file_id = data.get("arguments", {}).get("file_id")
                if not file_id:
                    raise ValueError("File ID required for delete")
                result = await handler.delete_file(file_id)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Format response
            return ToolResponse(
                content=[
                    Content(
                        type=ContentType.TEXT,
                        text=json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                    )
                ]
            )
        
    except Exception as e:
        logger.error(f"Error invoking tool {tool_name}: {str(e)}")
        error_response = {
            "content": [
                Content(
                    type=ContentType.TEXT,
                    text=str(e)
                )
            ],
            "isError": True
        }
        
        # Add stack trace in debug mode
        if server_settings['debugMode']:
            error_response["content"].append(
                Content(
                    type=ContentType.TEXT,
                    text=f"Stack trace:\n{traceback.format_exc()}"
                )
            )
            logger.debug(f"Full stack trace:\n{traceback.format_exc()}")
        
        return ToolResponse(**error_response)

@app.on_event("startup")
async def startup_event():
    await connection_manager.start_history_tracking()

@app.get("/api/status")
async def get_status():
    """Get current server status"""
    return connection_manager.get_status()

@app.get("/api/connections/history")
async def get_connection_history():
    """Get connection history for the last 30 minutes"""
    return connection_manager.get_history()

@app.get("/api/clients")
async def get_active_clients():
    """Get list of currently connected clients"""
    return connection_manager.get_active_clients()

@app.post("/api/clients/{client_id}/disconnect")
async def disconnect_client(client_id: str):
    """Disconnect a specific client"""
    if client_id in connection_manager.connected_clients:
        connection_manager.remove_client(client_id, "Manual disconnect")
        return {"message": f"Client {client_id} disconnected"}
    raise HTTPException(status_code=404, detail="Client not found")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    # If client is already connected, close the old connection
    if client_id in connection_manager.connected_clients:
        try:
            old_websocket = connection_manager.connected_clients[client_id]["websocket"]
            await old_websocket.close(code=1000, reason="New connection established")
            logger.info(f"Closed existing connection for client {client_id}")
        except Exception as e:
            logger.error(f"Error closing existing connection for {client_id}: {str(e)}")
        finally:
            connection_manager.remove_client(client_id, "New connection")
    
    await websocket.accept()
    
    if server_settings['debugMode']:
        logger.debug(f"New WebSocket connection from {client_id}")
        logger.debug(f"WebSocket headers: {dict(websocket.headers)}")
    
    # Register the new client
    client_info = {
        "user_agent": websocket.headers.get("user-agent"),
        "ip": websocket.client.host,
        "port": websocket.client.port
    } if server_settings['debugMode'] else {}
    
    connection_manager.add_client(client_id, websocket, dict(websocket.headers), client_info)
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                
                if server_settings['debugMode']:
                    logger.debug(f"Received WebSocket message from {client_id}: {data}")
                
                if data == "ping":
                    connection_manager.update_client_ping(client_id)
                    await websocket.send_text("pong")
                    if server_settings['debugMode']:
                        logger.debug(f"Sent pong response to {client_id}")
                
            except WebSocketDisconnect:
                raise  # Re-raise to handle in outer try/except
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {str(e)}")
                if server_settings['debugMode']:
                    logger.debug(f"Stack trace:\n{traceback.format_exc()}")
                continue  # Continue listening for messages
            
    except WebSocketDisconnect:
        if server_settings['debugMode']:
            logger.debug(f"WebSocket connection closed for {client_id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection for {client_id}: {str(e)}")
        if server_settings['debugMode']:
            logger.debug(f"Stack trace:\n{traceback.format_exc()}")
    finally:
        connection_manager.remove_client(client_id, "Connection closed")

@app.get("/api/services/{service_id}")
async def get_service_config(service_id: str):
    """Get configuration for a specific service"""
    if service_id not in service_configs:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    return service_configs[service_id]

@app.put("/api/services/{service_id}")
async def update_service_config(service_id: str, config: dict):
    """Update configuration for a specific service"""
    if service_id not in service_configs:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    service_configs[service_id] = config
    return {"message": f"Service {service_id} configuration updated"}

@app.post("/api/services/{service_id}/toggle")
async def toggle_service(service_id: str, data: dict):
    """Toggle a service on/off"""
    if service_id not in service_configs:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    service_configs[service_id]['enabled'] = data.get('enabled', False)
    return {"message": f"Service {service_id} {'enabled' if data.get('enabled') else 'disabled'}"}

@app.get("/api/settings")
async def get_settings():
    """Get server and MCP settings"""
    return {
        "server": server_settings,
        "mcp": mcp_settings
    }

@app.put("/api/settings")
async def update_settings(settings: dict):
    """Update server and MCP settings"""
    if 'server' in settings:
        # Check if debug mode is being changed
        if 'debugMode' in settings['server'] and settings['server']['debugMode'] != server_settings['debugMode']:
            set_debug_mode(settings['server']['debugMode'])
        server_settings.update(settings['server'])
    if 'mcp' in settings:
        mcp_settings.update(settings['mcp'])
    return {"message": "Settings updated successfully"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MCP Server with tools:")
    for tool in TOOLS:
        logger.info(f"  - {tool['name']} ({tool['display_name']})")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info") 