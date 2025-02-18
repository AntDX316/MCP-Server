from typing import Dict, Optional, List
import logging
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from .base import BaseServiceHandler

logger = logging.getLogger(__name__)

class AzureHandler(BaseServiceHandler):
    async def validate_config(self, config: Dict[str, str]) -> bool:
        """Validate Azure configuration"""
        required_fields = ['tenant_id', 'client_id', 'client_secret']
        return all(field in config and config[field] for field in required_fields)

    async def initialize(self) -> bool:
        """Initialize Azure clients"""
        try:
            credentials = ClientSecretCredential(
                tenant_id=self.config['tenant_id'],
                client_id=self.config['client_id'],
                client_secret=self.config['client_secret']
            )

            self._client = {
                'resource': ResourceManagementClient(credentials, self.config.get('subscription_id')),
                'compute': ComputeManagementClient(credentials, self.config.get('subscription_id')),
                'network': NetworkManagementClient(credentials, self.config.get('subscription_id'))
            }
            return True
        except Exception as e:
            logger.error(f"Azure initialization failed: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test Azure connection by listing resource groups"""
        if not self._client:
            return False

        try:
            # Try to list resource groups to test the connection
            list(self._client['resource'].resource_groups.list())
            logger.info("Azure connection successful")
            return True
        except Exception as e:
            logger.error(f"Azure connection test failed: {str(e)}")
            return False

    async def list_resource_groups(self) -> Optional[List[dict]]:
        """List Azure resource groups"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            resource_groups = []
            for group in self._client['resource'].resource_groups.list():
                resource_groups.append({
                    'id': group.id,
                    'name': group.name,
                    'location': group.location,
                    'tags': group.tags
                })
            return resource_groups
        except Exception as e:
            logger.error(f"Error listing resource groups: {str(e)}")
            return None

    async def list_virtual_machines(self, resource_group: str = None) -> Optional[List[dict]]:
        """List Azure virtual machines"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            vms = []
            if resource_group:
                vm_list = self._client['compute'].virtual_machines.list(resource_group_name=resource_group)
            else:
                vm_list = self._client['compute'].virtual_machines.list_all()

            for vm in vm_list:
                vms.append({
                    'id': vm.id,
                    'name': vm.name,
                    'location': vm.location,
                    'size': vm.hardware_profile.vm_size,
                    'os_type': vm.storage_profile.os_disk.os_type,
                    'status': vm.provisioning_state
                })
            return vms
        except Exception as e:
            logger.error(f"Error listing virtual machines: {str(e)}")
            return None

    async def start_vm(self, resource_group: str, vm_name: str) -> bool:
        """Start a virtual machine"""
        if not self.is_initialized:
            if not await self.setup():
                return False

        try:
            self._client['compute'].virtual_machines.begin_start(
                resource_group_name=resource_group,
                vm_name=vm_name
            ).result()
            return True
        except Exception as e:
            logger.error(f"Error starting VM: {str(e)}")
            return False

    async def stop_vm(self, resource_group: str, vm_name: str) -> bool:
        """Stop a virtual machine"""
        if not self.is_initialized:
            if not await self.setup():
                return False

        try:
            self._client['compute'].virtual_machines.begin_deallocate(
                resource_group_name=resource_group,
                vm_name=vm_name
            ).result()
            return True
        except Exception as e:
            logger.error(f"Error stopping VM: {str(e)}")
            return False

    async def get_vm_status(self, resource_group: str, vm_name: str) -> Optional[dict]:
        """Get virtual machine status"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            instance_view = self._client['compute'].virtual_machines.instance_view(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            status = {
                'name': vm_name,
                'statuses': [status.display_status for status in instance_view.statuses],
                'power_state': next((status.display_status for status in instance_view.statuses 
                                   if status.code.startswith('PowerState')), None)
            }
            return status
        except Exception as e:
            logger.error(f"Error getting VM status: {str(e)}")
            return None

    async def close(self):
        """Close Azure clients"""
        self._client = None
        self._initialized = False 