from typing import Dict, Optional
import aiohttp
import logging
from .base import BaseServiceHandler

logger = logging.getLogger(__name__)

class GitHubHandler(BaseServiceHandler):
    GITHUB_API_URL = "https://api.github.com"

    async def validate_config(self, config: Dict[str, str]) -> bool:
        """Validate GitHub configuration"""
        required_fields = ['access_token', 'organization']
        return all(field in config and config[field] for field in required_fields)

    async def initialize(self) -> bool:
        """Initialize GitHub client"""
        try:
            self._client = aiohttp.ClientSession(headers={
                'Authorization': f'token {self.config["access_token"]}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'MCP-Server'
            })
            return True
        except Exception as e:
            logger.error(f"GitHub initialization failed: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test GitHub connection by fetching user information"""
        if not self._client:
            return False

        try:
            async with self._client.get(f"{self.GITHUB_API_URL}/user") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"GitHub connection successful - authenticated as {data.get('login')}")
                    return True
                else:
                    logger.error(f"GitHub connection failed - status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"GitHub connection test failed: {str(e)}")
            return False

    async def get_repositories(self) -> Optional[list]:
        """Get list of repositories for the configured organization"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            org = self.config['organization']
            async with self._client.get(f"{self.GITHUB_API_URL}/orgs/{org}/repos") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch repositories - status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            return None

    async def get_repository_content(self, repo: str, path: str = "") -> Optional[list]:
        """Get contents of a repository path"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            org = self.config['organization']
            url = f"{self.GITHUB_API_URL}/repos/{org}/{repo}/contents/{path}"
            async with self._client.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch repository content - status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching repository content: {str(e)}")
            return None

    async def create_issue(self, repo: str, title: str, body: str, labels: list = None) -> Optional[dict]:
        """Create an issue in a repository"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            org = self.config['organization']
            url = f"{self.GITHUB_API_URL}/repos/{org}/{repo}/issues"
            data = {
                "title": title,
                "body": body,
            }
            if labels:
                data["labels"] = labels

            async with self._client.post(url, json=data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    logger.error(f"Failed to create issue - status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            return None

    async def close(self):
        """Close the aiohttp session"""
        if self._client:
            await self._client.close()
            self._client = None
            self._initialized = False 