"""Encryption utilities for sensitive data."""

import os
import base64
from cryptography.fernet import Fernet
from typing import Optional


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize with encryption key from environment."""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        
        # Ensure key is proper length for Fernet (32 bytes, base64 encoded)
        if len(encryption_key) == 32:
            # If it's exactly 32 chars, encode it
            key = base64.urlsafe_b64encode(encryption_key.encode())
        else:
            # Assume it's already base64 encoded
            key = encryption_key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        if not data:
            return ""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded data and return original string."""
        if not encrypted_data:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            raise ValueError("Failed to decrypt data - invalid format or key")
    
    def mask_key(self, api_key: str, visible_chars: int = 8) -> str:
        """Mask an API key for display purposes."""
        if not api_key or len(api_key) <= visible_chars:
            return "*" * 12
        return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)


# Global instance
encryption_service = EncryptionService()
