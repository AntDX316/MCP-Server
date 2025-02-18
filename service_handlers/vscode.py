from typing import Dict, Optional
import logging
import json
import os
from pathlib import Path
from .base import BaseServiceHandler

logger = logging.getLogger(__name__)

class VSCodeHandler(BaseServiceHandler):
    async def validate_config(self, config: Dict[str, str]) -> bool:
        """VS Code doesn't require configuration"""
        return True

    async def initialize(self) -> bool:
        """Initialize VS Code integration"""
        try:
            # Create a settings file for VS Code integration
            settings_dir = Path(".vscode")
            settings_dir.mkdir(exist_ok=True)
            
            settings_file = settings_dir / "mcp-settings.json"
            settings = {
                "mcp.server.enabled": True,
                "mcp.server.url": "ws://localhost:8000/ws",
                "mcp.server.autoConnect": True
            }
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            self._client = {
                'settings_file': settings_file,
                'settings': settings
            }
            return True
        except Exception as e:
            logger.error(f"VS Code initialization failed: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test VS Code integration"""
        if not self._client:
            return False

        try:
            # Check if settings file exists and is readable
            settings_file = self._client['settings_file']
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    if settings.get('mcp.server.enabled'):
                        logger.info("VS Code integration is properly configured")
                        return True
            return False
        except Exception as e:
            logger.error(f"VS Code connection test failed: {str(e)}")
            return False

    async def update_settings(self, settings: Dict[str, any]) -> bool:
        """Update VS Code settings"""
        if not self.is_initialized:
            if not await self.setup():
                return False

        try:
            current_settings = self._client['settings']
            current_settings.update(settings)
            
            with open(self._client['settings_file'], 'w') as f:
                json.dump(current_settings, f, indent=2)
            
            self._client['settings'] = current_settings
            return True
        except Exception as e:
            logger.error(f"Error updating VS Code settings: {str(e)}")
            return False

    async def get_settings(self) -> Optional[Dict[str, any]]:
        """Get current VS Code settings"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            return self._client['settings']
        except Exception as e:
            logger.error(f"Error getting VS Code settings: {str(e)}")
            return None

    async def create_workspace_file(self, workspace_name: str, folders: list) -> bool:
        """Create a VS Code workspace file"""
        if not self.is_initialized:
            if not await self.setup():
                return False

        try:
            workspace = {
                "folders": [{"path": folder} for folder in folders],
                "settings": self._client['settings']
            }
            
            workspace_file = Path(f"{workspace_name}.code-workspace")
            with open(workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error creating workspace file: {str(e)}")
            return False

    async def close(self):
        """Clean up VS Code integration"""
        self._client = None
        self._initialized = False 