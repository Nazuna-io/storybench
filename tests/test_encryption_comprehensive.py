"""Comprehensive tests for encryption utilities."""

import pytest
import os
import base64
from unittest.mock import patch
from cryptography.fernet import Fernet

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.utils.encryption import EncryptionService


class TestEncryptionServiceExtended:
    """Extended tests for EncryptionService."""
    
    def setup_method(self):
        """Set up test environment."""
        # Generate a valid test key
        self.test_key = Fernet.generate_key().decode()
        
    def test_initialization_with_32_char_key(self):
        """Test initialization with 32 character key."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'a' * 32}):
            service = EncryptionService()
            assert service.cipher is not None
            
    def test_initialization_with_base64_key(self):
        """Test initialization with base64 encoded key."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            assert service.cipher is not None
            
    def test_encrypt_decrypt_with_unicode(self):
        """Test encryption/decryption with unicode characters."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            test_data = "Hello 世界! 🌟"
            encrypted = service.encrypt(test_data)
            decrypted = service.decrypt(encrypted)
            
            assert decrypted == test_data
            assert encrypted != test_data
            assert len(encrypted) > 0
            
    def test_encrypt_decrypt_long_string(self):
        """Test encryption/decryption with long strings."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            test_data = "x" * 10000  # Very long string
            encrypted = service.encrypt(test_data)
            decrypted = service.decrypt(encrypted)
            
            assert decrypted == test_data
            
    def test_decrypt_invalid_data(self):
        """Test decryption with invalid data."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            with pytest.raises(ValueError, match="Failed to decrypt data"):
                service.decrypt("invalid_encrypted_data")
                
    def test_decrypt_corrupted_base64(self):
        """Test decryption with corrupted base64 data."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            with pytest.raises(ValueError, match="Failed to decrypt data"):
                service.decrypt("corrupted!")
                
    def test_mask_key_openai_project(self):
        """Test masking OpenAI project keys."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "sk-proj-1234567890abcdef"
            masked = service.mask_key(api_key)
            
            assert masked.startswith("sk-proj-123")
            assert masked.endswith("*" * (len(api_key) - 11))
            
    def test_mask_key_anthropic_api03(self):
        """Test masking Anthropic API03 keys."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "sk-ant-api03-1234567890abcdef"
            masked = service.mask_key(api_key)
            
            assert masked.startswith("sk-ant-api03-")
            assert masked.endswith("*" * (len(api_key) - 14))
            
    def test_mask_key_anthropic_regular(self):
        """Test masking regular Anthropic keys."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "sk-ant-1234567890abcdef"
            masked = service.mask_key(api_key)
            
            assert masked.startswith("sk-ant-12")
            assert masked.endswith("*" * (len(api_key) - 10))
            
    def test_mask_key_google(self):
        """Test masking Google API keys."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "AIzaSyDbKE1234567890abcdef"
            masked = service.mask_key(api_key)
            
            assert masked.startswith("AIzaSyDbKE")
            assert masked.endswith("*" * (len(api_key) - 10))
            
    def test_mask_key_generic(self):
        """Test masking generic API keys."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "generic-1234567890abcdef"
            masked = service.mask_key(api_key)
            
            assert masked.startswith("generic-")
            assert masked.endswith("*" * (len(api_key) - 8))
            
    def test_mask_key_custom_visible_chars(self):
        """Test masking with custom visible characters."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "test-1234567890"
            masked = service.mask_key(api_key, visible_chars=5)
            
            assert masked == "test-*******"
            
    def test_mask_key_short_key(self):
        """Test masking short API keys."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            api_key = "short"
            masked = service.mask_key(api_key)
            
            assert masked == "*****"
            
    def test_encryption_consistency(self):
        """Test that the same data produces different encrypted results."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': self.test_key}):
            service = EncryptionService()
            
            test_data = "test_data"
            encrypted1 = service.encrypt(test_data)
            encrypted2 = service.encrypt(test_data)
            
            # Should be different due to randomization
            assert encrypted1 != encrypted2
            
            # But both should decrypt to same value
            assert service.decrypt(encrypted1) == test_data
            assert service.decrypt(encrypted2) == test_data
