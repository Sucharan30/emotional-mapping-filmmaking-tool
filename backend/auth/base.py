"""
auth/base.py — Abstract interface for authentication providers.

To swap the auth provider:
  1. Create a new file, e.g. auth/custom_auth.py
  2. Implement AuthProvider
  3. Update _auth_provider in auth/dependencies.py
No changes needed in routers or services.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AuthUser:
    """Verified user identity returned by any auth provider."""
    id: uuid.UUID
    email: str


class AuthProvider(ABC):
    """
    Interface for backend-side token verification.

    The frontend handles the full OTP flow with supabase-js:
      1. signInWithOtp({ email })
      2. verifyOtp({ email, token, type: 'email' })
    The backend never touches OTP codes or passwords.
    Its only job is to verify the access_token on each request.
    """

    @abstractmethod
    async def verify_token(self, token: str) -> AuthUser:
        """
        Verify a JWT access token and return the authenticated user.

        Args:
            token: The raw Bearer token string.

        Returns:
            AuthUser with verified id and email.

        Raises:
            AuthenticationError: If the token is invalid, expired, or
                                 the auth service is unreachable.
        """
        raise NotImplementedError


class AuthenticationError(Exception):
    """Raised when a token cannot be verified."""

    def __init__(self, message: str = "Invalid or expired authentication token.") -> None:
        super().__init__(message)
        self.message = message
