#!/usr/bin/env python3
"""Fix APIEvaluator to handle o4-mini parameter correctly"""

import re

# Read the file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'r') as f:
    content = f.read()

# Fix 1: Setup method
old_setup = '''                # Test with a minimal request
                await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=1
                )'''

new_setup = '''                # Test with a minimal request
                if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
                    await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": "Test"}],
                        max_completion_tokens=1
                    )
                else:
                    await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=1
                    )'''

content = content.replace(old_setup, new_setup)

# Fix 2: Generation method
old_generate = '''    async def _generate_openai(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.9),
            max_tokens=kwargs.get("max_tokens", 4096)
        )
        return response.choices[0].message.content'''

new_generate = '''    async def _generate_openai(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        
        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.9)
        }
        
        # Use appropriate token parameter based on model
        if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
            request_params["max_completion_tokens"] = kwargs.get("max_completion_tokens", kwargs.get("max_tokens", 4096))
        else:
            request_params["max_tokens"] = kwargs.get("max_tokens", 4096)
        
        response = await self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content'''

content = content.replace(old_generate, new_generate)

# Write the fixed file
with open('/home/todd/storybench/src/storybench/evaluators/api_evaluator.py', 'w') as f:
    f.write(content)

print("✅ APIEvaluator fixed for o4-mini support")
