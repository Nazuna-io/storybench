"""API-based LLM evaluator for OpenAI, Anthropic, Google, and other services."""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
import openai
import anthropic
import google.generativeai as genai
from .base import BaseEvaluator


class APIEvaluator(BaseEvaluator):
    """Evaluator for API-based LLM services."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize API evaluator."""
        super().__init__(name, config)
        self.api_keys = api_keys
        self.provider = config.get("provider", "").lower()
        self.model_name = config.get("model_name", "")
        self.client = None
        
    async def setup(self) -> bool:
        """Setup API client and test connection."""
        try:
            if self.provider == "openai":
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_keys.get("OPENAI_API_KEY")
                )
                await self._test_openai_connection()
                
            elif self.provider == "anthropic":
                self.client = anthropic.AsyncAnthropic(
                    api_key=self.api_keys.get("ANTHROPIC_API_KEY")
                )
                await self._test_anthropic_connection()
                
            elif self.provider == "gemini":
                genai.configure(api_key=self.api_keys.get("GOOGLE_API_KEY"))
                self.client = genai.GenerativeModel(self.model_name)
                await self._test_gemini_connection()
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            self.is_setup = True
            return True            
        except Exception as e:
            print(f"Failed to setup {self.name}: {e}")
            return False
            
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using the appropriate API."""
        if not self.is_setup:
            raise RuntimeError(f"Evaluator {self.name} not setup")
            
        start_time = time.time()
        
        try:
            if self.provider == "openai":
                response_text = await self._generate_openai(prompt, **kwargs)
            elif self.provider == "anthropic":
                response_text = await self._generate_anthropic(prompt, **kwargs)
            elif self.provider == "gemini":
                response_text = await self._generate_gemini(prompt, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            return self._create_response_dict(response_text, start_time)
            
        except Exception as e:
            return self._create_response_dict(
                f"Error generating response: {str(e)}", 
                start_time, 
                {"error": True}
            )
            
    async def cleanup(self) -> None:
        """Clean up API connections."""
        if self.client:
            # Close any persistent connections
            if hasattr(self.client, 'close'):
                await self.client.close()
        self.client = None
        self.is_setup = False
    async def _generate_openai(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.9),
            max_tokens=kwargs.get("max_tokens", 4096)
        )
        return response.choices[0].message.content
        
    async def _generate_anthropic(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API."""
        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.9),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
        
    async def _generate_gemini(self, prompt: str, **kwargs) -> str:
        """Generate response using Gemini API."""
        response = await self.client.generate_content_async(prompt)
        return response.text
        
    async def _test_openai_connection(self) -> None:
        """Test OpenAI API connection."""
        await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1
        )
        
    async def _test_anthropic_connection(self) -> None:
        """Test Anthropic API connection."""
        await self.client.messages.create(
            model=self.model_name,
            max_tokens=1,
            messages=[{"role": "user", "content": "Test"}]
        )
        
    async def _test_gemini_connection(self) -> None:
        """Test Gemini API connection."""
        await self.client.generate_content_async("Test")
