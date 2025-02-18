import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sse_connection(url="http://localhost:8765/sse"):
    """Simple SSE client to test the connection"""
    headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                logger.info(f"Connected to SSE endpoint: {response.status}")
                
                # Keep connection alive for 15 seconds
                start_time = datetime.now()
                duration = 15  # seconds
                
                while (datetime.now() - start_time).seconds < duration:
                    try:
                        line = await response.content.readline()
                        if line:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                data = json.loads(line[6:])
                                if "type" in data and data["type"] == "capabilities":
                                    logger.info("\n=== Capabilities Message ===")
                                    for tool in data["capabilities"]["tools"]:
                                        logger.info(f"Tool: {tool['name']} ({tool['display_name']})")
                                        logger.info(f"Description: {tool['description']}")
                                        logger.info("---")
                                elif "event" in data and data["event"] == "heartbeat":
                                    heartbeat_data = json.loads(data["data"])
                                    logger.info(f"Heartbeat received at: {heartbeat_data['timestamp']}")
                                else:
                                    logger.info(f"Other message received: {json.dumps(data, indent=2)}")
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        continue
                
                logger.info("Test completed - closing connection")
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_sse_connection()) 