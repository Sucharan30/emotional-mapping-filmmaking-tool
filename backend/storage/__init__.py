"""
storage/__init__.py — Storage package initialization.

Provides a factory function `get_storage()` that returns the
configured StorageProvider.
"""

from storage.base import StorageError, StorageProvider
from storage.supabase_storage import SupabaseStorageProvider


def get_storage() -> StorageProvider:
    """
    Returns the configured StorageProvider instance.
    Currently defaults to SupabaseStorageProvider.
    """
    return SupabaseStorageProvider()


__all__ = [
    "StorageError",
    "StorageProvider",
    "get_storage",
]
