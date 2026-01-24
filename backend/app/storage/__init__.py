"""Storage providers."""

from typing import Protocol, BinaryIO

from app.config import get_settings


class StorageProvider(Protocol):
    """Protocol for storage providers."""

    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        client_id: int,
        period_id: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file and return the storage key."""
        ...

    def download_file(self, key: str) -> bytes:
        """Download a file by its key."""
        ...

    def get_presigned_url(
        self, key: str, expiration: int = 3600, for_upload: bool = False
    ) -> str:
        """Get a URL for accessing the file."""
        ...

    def delete_file(self, key: str) -> bool:
        """Delete a file by its key."""
        ...

    def file_exists(self, key: str) -> bool:
        """Check if a file exists."""
        ...

    def get_file_metadata(self, key: str) -> dict:
        """Get metadata for a file."""
        ...


def get_storage() -> StorageProvider:
    """Get the configured storage provider."""
    settings = get_settings()

    if settings.storage_provider == "uploadthing":
        from app.storage.uploadthing import UploadThingStorage
        return UploadThingStorage()
    else:
        from app.storage.s3 import S3Storage
        return S3Storage()
