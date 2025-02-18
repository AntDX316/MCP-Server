from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import services
from datetime import datetime
from enum import Enum

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

app = FastAPI(title="MCP Server for Cursor")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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

@app.get("/sse")
async def sse(request: Request):
    """SSE endpoint that sends capabilities and heartbeat messages"""
    async def event_generator():
        # Send initial capabilities message
        capabilities = {
            "type": "capabilities",
            "tools": TOOLS,
            "resources": [],
            "prompts": []
        }
        yield {
            "event": "message",
            "data": json.dumps(capabilities)
        }
        
        # Send heartbeat every 5 seconds
        while True:
            try:
                await asyncio.sleep(5)
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.now().isoformat()})
                }
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
        return ToolResponse(
            content=[
                Content(
                    type=ContentType.TEXT,
                    text=str(e)
                )
            ],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MCP Server with tools:")
    for tool in TOOLS:
        logger.info(f"  - {tool['name']} ({tool['display_name']})")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info") 