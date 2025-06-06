"""
Tests for utility modules like encryption.
These tests cover utility functions and services.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Import the utilities we want to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.utils.encryption import EncryptionService


class TestEncryptionService:
    """Test the EncryptionService utility."""
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test_key_12345678901234567890123'})
    def test_encryption_service_initialization(self):
        """Test that EncryptionService initializes properly with env key."""
        service = EncryptionService()
        assert service.cipher is not None
    
    def test_encryption_service_no_key_raises_error(self):
        """Test that missing ENCRYPTION_KEY raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ENCRYPTION_KEY environment variable is required"):
                EncryptionService()
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test_key_12345678901234567890123'})
    def test_encrypt_decrypt_roundtrip(self):
        """Test that we can encrypt and decrypt data successfully."""
        service = EncryptionService()
        
        original_data = "sensitive_api_key_12345"
        encrypted = service.encrypt(original_data)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original_data
        assert encrypted != original_data  # Make sure it's actually encrypted
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test_key_12345678901234567890123'})
    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        service = EncryptionService()
        
        # Check what the method returns for empty string
        result = service.encrypt("")
        assert result == ""  # Based on the code logic
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test_key_12345678901234567890123'})
    def test_encrypt_none_value(self):
        """Test encrypting None value."""
        service = EncryptionService()
        
        # Check what the method returns for None
        result = service.encrypt(None)
        assert result == ""  # Based on the code logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
