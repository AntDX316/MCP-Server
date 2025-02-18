from pydantic import BaseModel
from typing import Dict, Optional
import json
import os
from pathlib import Path

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    max_connections: int = 100
    ping_timeout: int = 30
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None

class MCPConfig(BaseModel):
    protocol_version: str = "1.0.0"
    allowed_models: list = []
    max_context_length: int = 4096
    default_temperature: float = 0.7
    max_tokens: int = 2048

class Config:
    def __init__(self):
        self.config_file = Path("config.json")
        self.server = ServerConfig()
        self.mcp = MCPConfig()
        self.load_config()

    def load_config(self):
        """Load configuration from file if it exists"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self.server = ServerConfig(**data.get("server", {}))
                self.mcp = MCPConfig(**data.get("mcp", {}))

    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            "server": self.server.dict(),
            "mcp": self.mcp.dict()
        }
        with open(self.config_file, "w") as f:
            json.dump(config_data, f, indent=4)

    def update_server_config(self, updates: Dict):
        """Update server configuration with new values"""
        current_data = self.server.dict()
        current_data.update(updates)
        self.server = ServerConfig(**current_data)
        self.save_config()

    def update_mcp_config(self, updates: Dict):
        """Update MCP configuration with new values"""
        current_data = self.mcp.dict()
        current_data.update(updates)
        self.mcp = MCPConfig(**current_data)
        self.save_config()

# Create a global config instance
config = Config() 