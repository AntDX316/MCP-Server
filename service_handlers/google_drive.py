from typing import Dict, Optional, List
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json
from .base import BaseServiceHandler
from pathlib import Path

logger = logging.getLogger(__name__)

class GoogleDriveHandler(BaseServiceHandler):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    async def validate_config(self, config: Dict[str, str]) -> bool:
        """Validate Google Drive configuration"""
        required_fields = ['client_id', 'client_secret']
        return all(field in config and config[field] for field in required_fields)

    async def initialize(self) -> bool:
        """Initialize Google Drive client"""
        try:
            credentials = None
            # Create tokens directory if it doesn't exist
            tokens_dir = Path("tokens")
            tokens_dir.mkdir(exist_ok=True)
            
            token_path = tokens_dir / f"google_drive_{self.service_id}.json"

            # Load existing token
            try:
                with open(token_path, 'r') as token_file:
                    token_data = json.load(token_file)
                    credentials = Credentials.from_authorized_user_info(token_data, self.SCOPES)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # If credentials are invalid or don't exist, create new ones
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": self.config['client_id'],
                                "client_secret": self.config['client_secret'],
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
                            }
                        },
                        self.SCOPES
                    )
                    credentials = flow.run_local_server(port=0)

                # Save the credentials
                with open(token_path, 'w') as token_file:
                    token_data = json.loads(credentials.to_json())
                    json.dump(token_data, token_file)

            self._client = build('drive', 'v3', credentials=credentials)
            return True
        except Exception as e:
            logger.error(f"Google Drive initialization failed: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Test Google Drive connection"""
        if not self._client:
            return False

        try:
            # Try to list files (limit to 1) to test the connection
            self._client.files().list(pageSize=1).execute()
            logger.info("Google Drive connection successful")
            return True
        except Exception as e:
            logger.error(f"Google Drive connection test failed: {str(e)}")
            return False

    async def list_files(self, folder_id: str = None, page_size: int = 10) -> Optional[List[dict]]:
        """List files in Google Drive"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            query = f"'{folder_id}' in parents" if folder_id else None
            results = self._client.files().list(
                pageSize=page_size,
                q=query,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return None

    async def upload_file(self, file_content: bytes, filename: str, mime_type: str, folder_id: str = None) -> Optional[dict]:
        """Upload a file to Google Drive"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            file_metadata = {
                'name': filename
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )

            file = self._client.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, webViewLink'
            ).execute()

            return file
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None

    async def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Optional[dict]:
        """Create a new folder in Google Drive"""
        if not self.is_initialized:
            if not await self.setup():
                return None

        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            folder = self._client.files().create(
                body=file_metadata,
                fields='id, name, mimeType, webViewLink'
            ).execute()

            return folder
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return None

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if not self.is_initialized:
            if not await self.setup():
                return False

        try:
            self._client.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

    async def close(self):
        """Close the Google Drive client"""
        self._client = None
        self._initialized = False 