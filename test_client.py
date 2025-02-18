import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.DEBUG)
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
                        if not line:
                            continue
                            
                        line = line.decode('utf-8').strip()
                        logger.debug(f"Raw SSE line: {line}")
                        
                        if line.startswith('data: '):
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            logger.debug(f"Parsed data: {json.dumps(data, indent=2)}")
                            
                            if data.get("type") == "capabilities":
                                logger.info("\n=== Capabilities Message ===")
                                for tool in data["capabilities"]["tools"]:
                                    logger.info(f"Tool: {tool['name']} ({tool['display_name']})")
                                    logger.info(f"Description: {tool['description']}")
                                    logger.info("---")
                            elif data.get("type") == "heartbeat":
                                logger.info(f"Heartbeat received at: {data['timestamp']}")
                            else:
                                logger.info(f"Other message received: {json.dumps(data, indent=2)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON: {str(e)}")
                        logger.debug(f"Problematic line: {line}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        continue
                
                logger.info("Test completed - closing connection")
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_sse_connection()) 