import asyncio
import websockets
import json
import uuid
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, server_url="ws://localhost:8000/ws"):
        self.server_url = server_url
        self.client_id = str(uuid.uuid4())
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to the MCP server"""
        try:
            self.websocket = await websockets.connect(f"{self.server_url}/{self.client_id}")
            self.running = True
            logger.info(f"Connected to server with client ID: {self.client_id}")
            return True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
            self.running = False
            logger.info("Disconnected from server")

    async def send_ping(self):
        """Send ping message to server"""
        if self.websocket:
            message = {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.websocket.send(json.dumps(message))

    async def run(self):
        """Main client loop"""
        if not await self.connect():
            return

        try:
            while self.running:
                try:
                    # Send ping every 10 seconds
                    await self.send_ping()
                    
                    # Wait for response
                    response = await self.websocket.recv()
                    logger.info(f"Received: {response}")
                    
                    # Wait before next ping
                    await asyncio.sleep(10)
                except websockets.exceptions.ConnectionClosed:
                    logger.error("Connection closed by server")
                    break
                except Exception as e:
                    logger.error(f"Error in client loop: {str(e)}")
                    break
        finally:
            await self.disconnect()

async def main():
    client = MCPClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main()) 