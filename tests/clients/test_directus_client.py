"""Tests for Directus client."""

import pytest
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.storybench.clients.directus_client import (
    DirectusClient, DirectusClientError, DirectusAuthenticationError,
    DirectusNotFoundError, DirectusServerError
)
from src.storybench.clients.directus_models import (
    DirectusPromptSetVersion, DirectusPromptSequence, DirectusPrompt,
    PublicationStatus, StorybenchPromptsStructure
)


class TestDirectusClient:
    """Test suite for DirectusClient."""
    
    @pytest.fixture
    def client(self):
        """Create a test DirectusClient instance."""
        return DirectusClient(
            base_url="https://test-directus.com",
            token="test-token",
            timeout=30
        )
    
    def test_init_with_params(self):
        """Test DirectusClient initialization with parameters."""
        client = DirectusClient(
            base_url="https://example.com",
            token="abc123",
            timeout=45
        )
        assert client.base_url == "https://example.com"
        assert client.token == "abc123"
        assert client.timeout == 45
    
    def test_init_with_env_vars(self):
        """Test DirectusClient initialization with environment variables."""
        with patch.dict(os.environ, {
            'DIRECTUS_URL': 'https://env-test.com',
            'DIRECTUS_TOKEN': 'env-token'
        }):
            client = DirectusClient()
            assert client.base_url == "https://env-test.com"
            assert client.token == "env-token"
    
    def test_init_missing_url(self):
        """Test DirectusClient initialization with missing URL."""
        with pytest.raises(DirectusClientError, match="Directus URL not provided"):
            DirectusClient(token="test-token")
    
    def test_init_missing_token(self):
        """Test DirectusClient initialization with missing token."""
        with pytest.raises(DirectusClientError, match="Directus token not provided"):
            DirectusClient(base_url="https://test.com")
    
    def test_base_url_trailing_slash_removal(self):
        """Test that trailing slash is removed from base URL."""
        client = DirectusClient(
            base_url="https://test.com/",
            token="test-token"
        )
        assert client.base_url == "https://test.com"
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client):
        """Test successful API request."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"data": "test"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            result = await client._make_request("GET", "/test")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_make_request_auth_error(self, client):
        """Test authentication error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.is_success = False
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            with pytest.raises(DirectusAuthenticationError):
                await client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_not_found_error(self, client):
        """Test not found error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.is_success = False
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            with pytest.raises(DirectusNotFoundError):
                await client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_server_error(self, client):
        """Test server error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.is_success = False
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            with pytest.raises(DirectusServerError):
                await client._make_request("GET", "/test")
