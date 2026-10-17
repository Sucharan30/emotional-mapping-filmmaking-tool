"""
storage/supabase_storage.py — Supabase implementation of StorageProvider.

Uses the supabase-py SDK. Note that the Python SDK does not currently
support fully async storage operations, so we run them in a threadpool
if necessary, or rely on the sync implementation where appropriate.
We will wrap the sync calls in asyncio.to_thread for non-blocking behavior.
"""

from __future__ import annotations

import asyncio
import io
import logging

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from config import settings
from storage.base import StorageError, StorageProvider

logger = logging.getLogger(__name__)


class SupabaseStorageProvider(StorageProvider):
    """
    Supabase Storage implementation.
    Requires SUPABASE_SERVICE_KEY if RLS restricts uploads.
    """

    def __init__(self) -> None:
        # We use the service key for backend storage operations to bypass RLS,
        # or the anon key if buckets are fully public/configured properly.
        # Prefer service_key if available.
        key = settings.supabase_service_key or settings.supabase_anon_key
        
        # Setting a reasonable timeout
        opts = ClientOptions(postgrest_client_timeout=10, storage_client_timeout=10)
        self._client: Client = create_client(settings.supabase_url, key, options=opts)

    async def upload_file(
        self,
        bucket: str,
        path: str,
        file_data: bytes | io.BytesIO,
        content_type: str,
    ) -> str:
        """Uploads a file to Supabase Storage."""
        if isinstance(file_data, io.BytesIO):
            file_data = file_data.getvalue()
            
        def _upload() -> None:
            try:
                self._client.storage.from_(bucket).upload(
                    file=file_data,
                    path=path,
                    file_options={"content-type": content_type, "upsert": "true"},
                )
            except Exception as exc:
                # The python SDK sometimes raises string exceptions or generic exceptions
                logger.error("Supabase upload failed: %s", exc)
                raise StorageError(f"Upload failed: {exc}")

        # Run sync SDK method in a thread pool to avoid blocking the event loop
        await asyncio.to_thread(_upload)
        
        return self.get_public_url(bucket, path)

    async def delete_file(self, bucket: str, path: str) -> None:
        """Deletes a file from Supabase Storage."""
        def _delete() -> None:
            try:
                self._client.storage.from_(bucket).remove([path])
            except Exception as exc:
                logger.error("Supabase delete failed: %s", exc)
                raise StorageError(f"Delete failed: {exc}")
                
        await asyncio.to_thread(_delete)

    def get_public_url(self, bucket: str, path: str) -> str:
        """Returns the public URL for a given path."""
        # This is a local string operation, no network call needed
        return self._client.storage.from_(bucket).get_public_url(path)
