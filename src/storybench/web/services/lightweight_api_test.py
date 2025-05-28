"""Lightweight API connectivity testing utilities."""

import aiohttp
import asyncio
import time
from typing import Dict, Optional, Tuple


class LightweightAPITester:
    """Lightweight API tester that doesn't require full model setup."""
    
    @staticmethod
    async def test_openai(api_key: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """Test OpenAI API connectivity."""
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use models endpoint for lightweight test
        url = "https://api.openai.com/v1/models"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return True, None, latency
                    elif response.status == 401:
                        return False, "Invalid API key", latency
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text[:100]}", latency
                        
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            return False, "Request timeout", latency
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return False, str(e), latency
    
    @staticmethod
    async def test_anthropic(api_key: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """Test Anthropic API connectivity."""
        start_time = time.time()
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Use a minimal completion request
        url = "https://api.anthropic.com/v1/messages"
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "Hi"}]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=15) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status in [200, 201]:
                        return True, None, latency
                    elif response.status == 401:
                        return False, "Invalid API key", latency
                    elif response.status == 403:
                        return False, "API key lacks required permissions", latency
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text[:100]}", latency
                        
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            return False, "Request timeout", latency
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return False, str(e), latency

    @staticmethod
    async def test_google(api_key: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """Test Google/Gemini API connectivity."""
        start_time = time.time()
        
        # Use the generateContent endpoint with minimal request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": "Hi"}]}],
            "generationConfig": {"maxOutputTokens": 1}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=15) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status in [200, 201]:
                        return True, None, latency
                    elif response.status == 403:
                        return False, "Invalid API key or insufficient permissions", latency
                    elif response.status == 400:
                        error_text = await response.text()
                        if "API_KEY_INVALID" in error_text:
                            return False, "Invalid API key", latency
                        return False, f"Bad request: {error_text[:100]}", latency
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text[:100]}", latency
                        
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            return False, "Request timeout", latency
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return False, str(e), latency
    
    @staticmethod
    async def test_deepinfra(api_key: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """Test DeepInfra API connectivity."""
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use a simple chat completions test with minimal model
        url = "https://api.deepinfra.com/v1/openai/chat/completions"
        
        payload = {
            "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return True, None, latency
                    elif response.status == 401:
                        return False, "Invalid API key", latency
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text}", latency
                        
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            return False, "Request timeout", latency
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return False, str(e), latency
    
    @staticmethod
    async def test_provider(provider: str, api_key: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """Test any supported provider."""
        if provider == "openai":
            return await LightweightAPITester.test_openai(api_key)
        elif provider == "anthropic":
            return await LightweightAPITester.test_anthropic(api_key)
        elif provider == "gemini":
            return await LightweightAPITester.test_google(api_key)
        elif provider == "deepinfra":
            return await LightweightAPITester.test_deepinfra(api_key)
        else:
            return False, f"Provider '{provider}' not supported for lightweight testing", 0.0
