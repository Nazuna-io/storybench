#!/usr/bin/env python3
"""
Quick API test for DeepSeek-R1-0528 model.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.evaluators.api_evaluator import APIEvaluator


async def test_api():
    """Test DeepSeek-R1-0528 API."""
    deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
    print(f"API key loaded: {bool(deepinfra_key)}")
    
    if not deepinfra_key:
        print("No API key - exiting")
        return
    
    config = {
        'name': 'DeepSeek-R1-0528',
        'type': 'api',
        'provider': 'deepinfra',
        'model_name': 'deepseek-ai/DeepSeek-R1-0528'
    }
    
    api_keys = {'deepinfra': deepinfra_key}
    
    try:
        evaluator = APIEvaluator('test', config, api_keys)
        await evaluator.setup()  # Initialize the evaluator
        
        # Test prompt with potential thinking text
        test_prompt = "What is 2+2? Think through this step by step."
        
        print(f"Testing {config['model_name']}...")
        response_dict = await evaluator.generate_response(test_prompt)
        response = response_dict.get('response', str(response_dict))
        
        print("✅ Response received!")
        print(f"Length: {len(response)} chars")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        # Check for thinking patterns
        thinking_indicators = ['<think>', '<thinking>', '[Thinking]', 'I need to think']
        found_thinking = any(indicator in response for indicator in thinking_indicators)
        
        if found_thinking:
            print("⚠️  Thinking text may still be present")
        else:
            print("✅ No obvious thinking text detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api())
