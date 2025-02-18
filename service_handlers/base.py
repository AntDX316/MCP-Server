from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseServiceHandler(ABC):
    def __init__(self, service_id: str, config: Dict[str, str]):
        self.service_id = service_id
        self.config = config
        self._client = None
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service with the current configuration"""
        pass

    @abstractmethod
    async def validate_config(self, config: Dict[str, str]) -> bool:
        """Validate the provided configuration"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the service"""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def client(self) -> Any:
        return self._client

    async def setup(self) -> bool:
        """Set up the service with error handling"""
        try:
            if not await self.validate_config(self.config):
                logger.error(f"{self.service_id}: Invalid configuration")
                return False

            if not await self.initialize():
                logger.error(f"{self.service_id}: Initialization failed")
                return False

            if not await self.test_connection():
                logger.error(f"{self.service_id}: Connection test failed")
                return False

            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"{self.service_id}: Setup failed - {str(e)}")
            return False

    def update_config(self, config: Dict[str, str]) -> None:
        """Update the service configuration"""
        self.config = config
        self._initialized = False
        self._client = None 