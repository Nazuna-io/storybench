    async def _generate_openai(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        
        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.9)
        }
        
        # Use appropriate token parameter based on model
        if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
            request_params["max_completion_tokens"] = kwargs.get("max_completion_tokens", 4096)
        else:
            request_params["max_tokens"] = kwargs.get("max_tokens", 4096)
        
        response = await self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content