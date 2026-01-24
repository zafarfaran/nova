"""UploadThing storage operations."""

import base64
import json
import uuid
from datetime import datetime
from typing import BinaryIO

import httpx

from app.config import get_settings


class UploadThingStorage:
    """UploadThing storage operations for document management."""

    BASE_URL = "https://api.uploadthing.com/v6"
    FILE_URL_BASE = "https://utfs.io/f"

    def __init__(self):
        self.settings = get_settings()
        self.token = self.settings.uploadthing_token
        self._api_key = self._extract_api_key()

    def _extract_api_key(self) -> str:
        """Extract API key from the UploadThing token."""
        try:
            decoded = base64.b64decode(self.token)
            data = json.loads(decoded)
            return data.get("apiKey", "")
        except Exception:
            return self.token

    def _get_headers(self) -> dict:
        """Get headers for UploadThing API requests."""
        return {
            "x-uploadthing-api-key": self._api_key,
            "Content-Type": "application/json",
        }

    def _generate_key(self, client_id: int, period_id: int, filename: str) -> str:
        """Generate a unique key for a document."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = filename.replace(" ", "_")
        return f"clients_{client_id}_periods_{period_id}_{timestamp}_{unique_id}_{safe_filename}"

    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        client_id: int,
        period_id: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to UploadThing and return the file key."""
        # Read file content
        file_content = file.read()
        file.seek(0)

        # Generate custom key for organizing files
        custom_id = self._generate_key(client_id, period_id, filename)

        # Step 1: Request upload URLs from UploadThing
        with httpx.Client() as client:
            # Request presigned URL
            response = client.post(
                f"{self.BASE_URL}/uploadFiles",
                headers=self._get_headers(),
                json={
                    "files": [
                        {
                            "name": filename,
                            "size": len(file_content),
                            "type": content_type,
                            "customId": custom_id,
                        }
                    ],
                    "acl": "public-read",
                    "contentDisposition": "inline",
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"Failed to get upload URL: {response.text}")

            data = response.json()
            if not data.get("data") or len(data["data"]) == 0:
                raise RuntimeError(f"No upload data returned: {response.text}")

            upload_data = data["data"][0]
            presigned_url = upload_data.get("url")
            file_key = upload_data.get("key")
            fields = upload_data.get("fields", {})

            # Step 2: Upload file to presigned URL
            # UploadThing uses multipart form upload
            files_data = {
                **fields,
                "file": (filename, file_content, content_type),
            }

            upload_response = client.post(
                presigned_url,
                files={"file": (filename, file_content, content_type)},
                data=fields,
            )

            if upload_response.status_code not in [200, 201, 204]:
                raise RuntimeError(f"Failed to upload file: {upload_response.text}")

            return file_key

    def download_file(self, file_key: str) -> bytes:
        """Download a file from UploadThing."""
        url = f"{self.FILE_URL_BASE}/{file_key}"

        with httpx.Client() as client:
            response = client.get(url)

            if response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_key}")
            if response.status_code != 200:
                raise RuntimeError(f"Failed to download file: {response.text}")

            return response.content

    def get_presigned_url(
        self, file_key: str, expiration: int = 3600, for_upload: bool = False
    ) -> str:
        """Get URL for a file. UploadThing files are public by default."""
        if for_upload:
            raise NotImplementedError("Use upload_file method for uploads")

        return f"{self.FILE_URL_BASE}/{file_key}"

    def delete_file(self, file_key: str) -> bool:
        """Delete a file from UploadThing."""
        with httpx.Client() as client:
            response = client.post(
                f"{self.BASE_URL}/deleteFiles",
                headers=self._get_headers(),
                json={"fileKeys": [file_key]},
            )

            if response.status_code != 200:
                raise RuntimeError(f"Failed to delete file: {response.text}")

            return True

    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in UploadThing."""
        url = f"{self.FILE_URL_BASE}/{file_key}"

        with httpx.Client() as client:
            response = client.head(url)
            return response.status_code == 200

    def get_file_metadata(self, file_key: str) -> dict:
        """Get metadata for a file in UploadThing."""
        url = f"{self.FILE_URL_BASE}/{file_key}"

        with httpx.Client() as client:
            response = client.head(url)

            if response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_key}")
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get file metadata: {response.text}")

            return {
                "content_type": response.headers.get("content-type"),
                "content_length": int(response.headers.get("content-length", 0)),
                "last_modified": response.headers.get("last-modified"),
                "etag": response.headers.get("etag"),
            }


def get_uploadthing_storage() -> UploadThingStorage:
    """Get an UploadThing storage instance."""
    return UploadThingStorage()
