from typing import Dict, List, Optional
from pydantic import BaseModel
import json
from pathlib import Path
import logging
import asyncio
from service_handlers import (
    GitHubHandler,
    SlackHandler,
    GoogleDriveHandler,
    AzureHandler,
    VSCodeHandler
)

logger = logging.getLogger(__name__)

class ServiceConfig(BaseModel):
    enabled: bool = False
    config: Dict[str, str] = {}

class ServicesManager:
    def __init__(self):
        self.config_file = Path("services_config.json")
        self.services: Dict[str, ServiceConfig] = {}
        self.handlers: Dict[str, object] = {}
        self.handler_classes = {
            'github': GitHubHandler,
            'slack': SlackHandler,
            'google_drive': GoogleDriveHandler,
            'azure': AzureHandler,
            'vscode': VSCodeHandler
        }
        self.load_config()

    def load_config(self):
        """Load services configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    for service_id, config in data.items():
                        self.services[service_id] = ServiceConfig(**config)
            except Exception as e:
                logger.error(f"Error loading services config: {str(e)}")
                # Initialize with empty config if loading fails
                self.services = {}
        else:
            # Initialize with empty config if file doesn't exist
            self.services = {}

    def save_config(self):
        """Save current services configuration to file"""
        try:
            config_data = {
                service_id: service_config.dict()
                for service_id, service_config in self.services.items()
            }
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving services config: {str(e)}")

    def get_service_config(self, service_id: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service"""
        return self.services.get(service_id)

    async def update_service_config(self, service_id: str, enabled: bool, config: Dict[str, str] = None):
        """Update configuration for a specific service"""
        try:
            # Get or create service config
            service_config = self.services.get(service_id)
            if service_config is None:
                service_config = ServiceConfig(enabled=False, config={})
                self.services[service_id] = service_config
            
            # If the service is being enabled
            if enabled and not service_config.enabled:
                if service_id in self.handler_classes:
                    handler_class = self.handler_classes[service_id]
                    handler = handler_class(service_id, config or {})
                    
                    # Validate and test the configuration
                    if not await handler.validate_config(config or {}):
                        raise ValueError(f"Invalid configuration for service {service_id}")
                    
                    if not await handler.setup():
                        raise ValueError(f"Failed to initialize service {service_id}")
                    
                    self.handlers[service_id] = handler
                else:
                    raise ValueError(f"Unknown service type: {service_id}")
            
            # If the service is being disabled
            elif not enabled and service_config.enabled:
                if service_id in self.handlers:
                    handler = self.handlers[service_id]
                    await handler.close()
                    del self.handlers[service_id]

            # Update the configuration
            service_config.enabled = enabled
            if config is not None:
                service_config.config = config
                if service_id in self.handlers and enabled:
                    self.handlers[service_id].update_config(config)

            self.services[service_id] = service_config
            self.save_config()
            
            logger.info(f"Service {service_id} configuration updated - enabled: {enabled}")
            return service_config
        except Exception as e:
            logger.error(f"Failed to update service {service_id}: {str(e)}")
            raise

    def get_all_services(self) -> Dict[str, ServiceConfig]:
        """Get configuration for all services"""
        return self.services

    def get_handler(self, service_id: str) -> Optional[object]:
        """Get the handler for a specific service"""
        return self.handlers.get(service_id)

    async def close_all(self):
        """Close all service handlers"""
        for service_id, handler in self.handlers.items():
            try:
                await handler.close()
            except Exception as e:
                logger.error(f"Error closing service {service_id}: {str(e)}")
        self.handlers.clear()

# Create a global services manager instance
services_manager = ServicesManager() 