import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPTestClient:
    def __init__(self, base_url="http://localhost:8765"):
        self.base_url = base_url
        self.ws_url = f"ws://{base_url.split('://')[-1]}/ws/{self.generate_client_id()}"
        self.sse_url = f"{base_url}/sse"
        self.running = False
        self.tools = []
        self.ws = None

    def generate_client_id(self):
        return f"test-client-{uuid.uuid4().hex[:8]}"

    async def connect(self):
        """Connect to both SSE and WebSocket endpoints"""
        self.running = True
        await asyncio.gather(
            self.connect_sse(),
            self.connect_ws()
        )

    async def connect_sse(self):
        """Connect to the SSE endpoint and process messages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.sse_url) as response:
                    logger.info(f"Connected to SSE endpoint: {response.status}")
                    
                    async for line in response.content:
                        if not self.running:
                            break
                        if line:
                            try:
                                decoded_line = line.decode('utf-8').strip()
                                if decoded_line.startswith('data: '):
                                    data = json.loads(decoded_line[6:])
                                    await self.handle_sse_message(data)
                            except Exception as e:
                                logger.error(f"Error processing SSE message: {str(e)}")
        except Exception as e:
            logger.error(f"SSE connection error: {str(e)}")

    async def connect_ws(self):
        """Connect to the WebSocket endpoint and handle messages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.ws_url) as ws:
                    self.ws = ws
                    logger.info("Connected to WebSocket endpoint")
                    
                    # Start ping loop
                    asyncio.create_task(self.ping_loop())
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data == 'pong':
                                logger.debug("Received pong")
                            else:
                                try:
                                    data = json.loads(msg.data)
                                    await self.handle_ws_message(data)
                                except json.JSONDecodeError:
                                    logger.error(f"Invalid JSON in WebSocket message: {msg.data}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket connection closed with error: {ws.exception()}")
                            break
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
        finally:
            self.ws = None

    async def ping_loop(self):
        """Send periodic pings to keep the connection alive"""
        while self.running and self.ws is not None:
            try:
                await self.ws.send_str('ping')
                logger.debug("Sent ping")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error sending ping: {str(e)}")
                break

    async def handle_sse_message(self, data):
        """Handle different types of SSE messages"""
        if isinstance(data, dict):
            if data.get("type") == "capabilities":
                self.tools = data.get("capabilities", {}).get("tools", [])
                logger.info(f"Received capabilities. Available tools: {[t['name'] for t in self.tools]}")
            elif "timestamp" in data:
                logger.debug(f"Received heartbeat: {data['timestamp']}")
            else:
                logger.info(f"Received SSE message: {data}")

    async def handle_ws_message(self, data):
        """Handle different types of WebSocket messages"""
        logger.info(f"Received WebSocket message: {data}")

    async def disconnect(self):
        """Disconnect from both SSE and WebSocket endpoints"""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("Disconnected from MCP Server")

    async def test_tool(self, message="Hello from test client!"):
        """Test the 'test' tool"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "arguments": {
                        "message": message
                    }
                }
                async with session.post(f"{self.base_url}/invoke/test", json=payload) as response:
                    result = await response.json()
                    logger.info(f"Test tool response: {result}")
                    return result
        except Exception as e:
            logger.error(f"Error testing tool: {str(e)}")
            return None

    async def test_google_drive(self, operation="list", **kwargs):
        """Test the Google Drive tool"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "arguments": {
                        "operation": operation,
                        **kwargs
                    }
                }
                async with session.post(f"{self.base_url}/invoke/google_drive", json=payload) as response:
                    result = await response.json()
                    logger.info(f"Google Drive tool response: {result}")
                    return result
        except Exception as e:
            logger.error(f"Error testing Google Drive: {str(e)}")
            return None

    async def run_tests(self):
        """Run a series of tests"""
        logger.info("Starting tests...")
        
        # Test SSE connection
        sse_task = asyncio.create_task(self.connect_sse())
        await asyncio.sleep(2)  # Wait for SSE connection and capabilities
        
        # Test the test tool
        logger.info("\nTesting 'test' tool...")
        await self.test_tool()
        
        # Test Google Drive list operation
        logger.info("\nTesting Google Drive list operation...")
        await self.test_google_drive(operation="list")
        
        # Keep running to receive SSE messages
        try:
            await sse_task
        except asyncio.CancelledError:
            logger.info("Tests completed")

async def main():
    client = MCPTestClient()
    try:
        await client.connect()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 