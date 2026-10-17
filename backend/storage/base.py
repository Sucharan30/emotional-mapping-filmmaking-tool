"""
storage/base.py — Abstract interface for object storage providers.

To swap the storage provider (e.g., from Supabase to AWS S3):
  1. Create a new file, e.g., storage/s3_storage.py
  2. Implement StorageProvider
  3. Update get_storage() in storage/__init__.py
No changes needed in routers or services.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from typing import Optional


class StorageError(Exception):
    """Raised when a storage operation fails."""
    def __init__(self, message: str = "Storage operation failed.") -> None:
        super().__init__(message)
        self.message = message


class StorageProvider(ABC):
    """
    Interface for file/blob storage operations.
    """

    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        path: str,
        file_data: bytes | io.BytesIO,
        content_type: str,
    ) -> str:
        """
        Uploads a file and returns its public URL.

        Args:
            bucket: The storage bucket name.
            path: The destination path/filename inside the bucket.
            file_data: The file content as bytes or BytesIO.
            content_type: MIME type (e.g., "video/mp4").

        Returns:
            The public URL of the uploaded file.

        Raises:
            StorageError: If the upload fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, bucket: str, path: str) -> None:
        """
        Deletes a file from storage.

        Args:
            bucket: The storage bucket name.
            path: The path/filename inside the bucket.

        Raises:
            StorageError: If the deletion fails.
        """
        raise NotImplementedError

    @abstractmethod
    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Generates the public URL for a file without uploading it.
        """
        raise NotImplementedError
