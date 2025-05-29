            if self.provider == "openai":
                self.client = openai.AsyncOpenAI(api_key=self.api_keys.get("openai"))
                # Test with a minimal request - use appropriate token parameter
                test_kwargs = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": "Test"}]
                }
                
                # Use max_completion_tokens for o3/o4 models, max_tokens for others
                if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
                    test_kwargs["max_completion_tokens"] = 1
                else:
                    test_kwargs["max_tokens"] = 1
                    
                await self.client.chat.completions.create(**test_kwargs)