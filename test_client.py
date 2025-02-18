import asyncio
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPTestClient:
    def __init__(self, sse_url="http://localhost:8765/sse", api_url="http://localhost:8765"):
        self.sse_url = sse_url
        self.api_url = api_url
        self.running = False
        self.tools = []

    async def connect_sse(self):
        """Connect to the SSE endpoint and process messages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.sse_url) as response:
                    logger.info(f"Connected to SSE endpoint: {response.status}")
                    
                    async for line in response.content:
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

    async def handle_sse_message(self, data):
        """Handle different types of SSE messages"""
        if isinstance(data, dict):
            if data.get("type") == "capabilities":
                self.tools = data.get("capabilities", {}).get("tools", [])
                logger.info(f"Received capabilities. Available tools: {[t['name'] for t in self.tools]}")
            elif "timestamp" in data:
                logger.info(f"Received heartbeat: {data['timestamp']}")
            else:
                logger.info(f"Received message: {data}")

    async def test_tool(self, message="Hello from test client!"):
        """Test the 'test' tool"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "arguments": {
                        "message": message
                    }
                }
                async with session.post(f"{self.api_url}/invoke/test", json=payload) as response:
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
                async with session.post(f"{self.api_url}/invoke/google_drive", json=payload) as response:
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
        await client.run_tests()
    except KeyboardInterrupt:
        logger.info("Test client stopped by user")

if __name__ == "__main__":
    asyncio.run(main()) 