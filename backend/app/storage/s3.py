"""S3 storage operations."""

import uuid
from datetime import datetime, timedelta
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings


class S3Storage:
    """S3 storage operations for document management."""

    def __init__(self):
        self.settings = get_settings()
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
            region_name=self.settings.aws_region,
        )
        self.bucket = self.settings.s3_bucket_name

    def _generate_key(self, client_id: int, period_id: int, filename: str) -> str:
        """Generate a unique S3 key for a document."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = filename.replace(" ", "_")
        return f"clients/{client_id}/periods/{period_id}/{timestamp}_{unique_id}_{safe_filename}"

    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        client_id: int,
        period_id: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to S3 and return the S3 key."""
        s3_key = self._generate_key(client_id, period_id, filename)

        try:
            self.client.upload_fileobj(
                file,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )
            return s3_key
        except ClientError as e:
            raise RuntimeError(f"Failed to upload file to S3: {e}")

    def download_file(self, s3_key: str) -> bytes:
        """Download a file from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {s3_key}")
            raise RuntimeError(f"Failed to download file from S3: {e}")

    def get_presigned_url(
        self, s3_key: str, expiration: int = 3600, for_upload: bool = False
    ) -> str:
        """Generate a presigned URL for download or upload."""
        try:
            if for_upload:
                url = self.client.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": self.bucket, "Key": s3_key},
                    ExpiresIn=expiration,
                )
            else:
                url = self.client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": s3_key},
                    ExpiresIn=expiration,
                )
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}")

    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            raise RuntimeError(f"Failed to delete file from S3: {e}")

    def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise RuntimeError(f"Failed to check file existence: {e}")

    def get_file_metadata(self, s3_key: str) -> dict:
        """Get metadata for a file in S3."""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File not found: {s3_key}")
            raise RuntimeError(f"Failed to get file metadata: {e}")


def get_s3_storage() -> S3Storage:
    """Get an S3 storage instance."""
    return S3Storage()
