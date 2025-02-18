from pydantic import BaseModel
from typing import Dict, Optional, List
import json
import os
from pathlib import Path

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    max_connections: int = 100
    ping_timeout: int = 30

class MCPServer(BaseModel):
    name: str
    type: str
    command: str
    args: List[str]
    env: Dict[str, str]

class MCPConfig(BaseModel):
    protocol_version: str = "1.0.0"
    allowed_models: list = []
    max_context_length: int = 4096
    default_temperature: float = 0.7
    max_tokens: int = 2048
    mcpServers: List[MCPServer] = []

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
                
                # Handle MCP servers configuration
                mcp_data = data.get("mcp", {})
                if "mcpServers" in mcp_data:
                    mcp_data["mcpServers"] = [
                        MCPServer(**server) for server in mcp_data["mcpServers"]
                    ]
                self.mcp = MCPConfig(**mcp_data)

    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            "server": self.server.dict(),
            "mcp": self.mcp.dict()
        }
        # Ensure the directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        # Write config with atomic operation
        temp_file = self.config_file.with_suffix('.tmp')
        with open(temp_file, "w") as f:
            json.dump(config_data, f, indent=4)
        temp_file.replace(self.config_file)

    def update_server_config(self, updates: Dict):
        """Update server configuration with new values"""
        current_data = self.server.dict()
        current_data.update(updates)
        self.server = ServerConfig(**current_data)
        self.save_config()  # Save immediately

    def update_mcp_config(self, updates: Dict):
        """Update MCP configuration with new values"""
        current_data = self.mcp.dict()
        
        # Handle MCP servers update
        if "mcpServers" in updates:
            updates["mcpServers"] = [
                MCPServer(**server) if isinstance(server, dict) else server
                for server in updates["mcpServers"]
            ]
            
        current_data.update(updates)
        self.mcp = MCPConfig(**current_data)
        self.save_config()  # Save immediately

# Create a global config instance
config = Config() 