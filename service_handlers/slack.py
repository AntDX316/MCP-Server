from typing import Dict, Optional
import aiohttp
import logging
from .base import BaseServiceHandler

logger = logging.getLogger(__name__)

class SlackHandler(BaseServiceHandler):
    SLACK_API_URL = "https://slack.com/api"

    async def validate_config(self, config: Dict[str, str]) -> bool:
        """Validate Slack configuration"""
        required_fields = ['bot_token', 'channel']
        return all(field in config and config[field] for field in required_fields)

    async def initialize(self) -> bool:
        """Initialize Slack client"""
        try:
            self._client = aiohttp.ClientSession(headers={
                'Authorization': f'Bearer {self.config["bot_token"]}',
                'Content-Type': 'application/json; charset=utf-8'
            })
            return True
        except Exception as e:
            logger.error(f"Slack initialization failed: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test Slack connection by checking auth"""
        if not self._client:
            return False

        try:
            async with self._client.get(f"{self.SLACK_API_URL}/auth.test") as response:
                data = await response.json()
                if data.get('ok'):
                    logger.info(f"Slack connection successful - authenticated as {data.get('user')}")
                    return True
                else:
                    logger.error(f"Slack connection failed - {data.get('error')}")
                    return False
        except Exception as e:
            logger.error(f"Slack connection test failed: {str(e)}")
            return False

    async def send_message(self, text: str, thread_ts: str = None, blocks: list = None) -> Optional[dict]:
        """Send a message to the configured channel"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            data = {
                "channel": self.config['channel'],
                "text": text
            }
            if thread_ts:
                data["thread_ts"] = thread_ts
            if blocks:
                data["blocks"] = blocks

            async with self._client.post(f"{self.SLACK_API_URL}/chat.postMessage", json=data) as response:
                result = await response.json()
                if result.get('ok'):
                    return result
                else:
                    logger.error(f"Failed to send message - {result.get('error')}")
                    return None
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return None

    async def get_channel_info(self) -> Optional[dict]:
        """Get information about the configured channel"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            channel = self.config['channel']
            # Remove the # if present
            if channel.startswith('#'):
                channel = channel[1:]

            async with self._client.get(
                f"{self.SLACK_API_URL}/conversations.info",
                params={"channel": channel}
            ) as response:
                result = await response.json()
                if result.get('ok'):
                    return result.get('channel')
                else:
                    logger.error(f"Failed to get channel info - {result.get('error')}")
                    return None
        except Exception as e:
            logger.error(f"Error getting channel info: {str(e)}")
            return None

    async def upload_file(self, file_content: bytes, filename: str, filetype: str = None, thread_ts: str = None) -> Optional[dict]:
        """Upload a file to the configured channel"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            data = aiohttp.FormData()
            data.add_field('channels', self.config['channel'])
            data.add_field('file', file_content, filename=filename)
            if filetype:
                data.add_field('filetype', filetype)
            if thread_ts:
                data.add_field('thread_ts', thread_ts)

            async with self._client.post(f"{self.SLACK_API_URL}/files.upload", data=data) as response:
                result = await response.json()
                if result.get('ok'):
                    return result
                else:
                    logger.error(f"Failed to upload file - {result.get('error')}")
                    return None
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None

    async def close(self):
        """Close the aiohttp session"""
        if self._client:
            await self._client.close()
            self._client = None
            self._initialized = False 