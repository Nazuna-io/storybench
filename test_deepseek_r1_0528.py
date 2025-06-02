#!/usr/bin/env python3
"""
Test script for DeepSeek-R1-0528 model integration and thinking text filtering.
"""

import os
import sys
import asyncio
import yaml

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.evaluators.api_evaluator import APIEvaluator


def test_thinking_filter():
    """Test the thinking text filtering function."""
    print("Testing thinking text filter...")
    
    # Create a dummy evaluator instance to test the filter
    config = {
        'name': 'DeepSeek-R1-0528',
        'type': 'api',
        'provider': 'deepinfra',
        'model_name': 'deepseek-ai/DeepSeek-R1-0528'
    }
    
    api_keys = {'deepinfra': 'dummy_key'}
    evaluator = APIEvaluator('test', config, api_keys)
    
    # Test cases for thinking text patterns
    test_cases = [
        {
            'input': '<think>This is reasoning text</think>\n\nActual response here.',
            'expected': 'Actual response here.'
        },
        {
            'input': '<thinking>Complex reasoning goes here</thinking>\n\nFinal answer: 42',
            'expected': 'Final answer: 42'
        },        {
            'input': '[Thinking]\nLet me analyze this step by step...\n[/Thinking]\n\nHere is my response.',
            'expected': 'Here is my response.'
        },
        {
            'input': 'Just a normal response without thinking tags.',
            'expected': 'Just a normal response without thinking tags.'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = evaluator._filter_thinking_text(case['input'])
        if result.strip() == case['expected'].strip():
            print(f"✅ Test case {i}: PASSED")
        else:
            print(f"❌ Test case {i}: FAILED")
            print(f"   Expected: {case['expected']!r}")
            print(f"   Got:      {result!r}")
    
    print()


def test_model_config():
    """Test that the model configuration is valid."""
    print("Testing model configuration...")
    
    # Load the models.yaml file
    try:
        with open('/home/todd/storybench/config/models.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if our new model is in the config
        deepseek_models = [
            model for model in config['models'] 
            if model.get('model_name', '').startswith('deepseek-ai/DeepSeek-R1')
        ]
        
        print(f"Found {len(deepseek_models)} DeepSeek models:")
        for model in deepseek_models:            print(f"  - {model['name']}: {model['model_name']}")
        
        # Verify our new model is there
        r1_0528_models = [
            model for model in deepseek_models 
            if 'DeepSeek-R1-0528' in model['model_name']
        ]
        
        if r1_0528_models:
            print("✅ DeepSeek-R1-0528 model found in configuration")
            model = r1_0528_models[0]
            print(f"   Name: {model['name']}")
            print(f"   Model: {model['model_name']}")
            print(f"   Provider: {model['provider']}")
            print(f"   Context size: {model.get('context_size', 'Not specified')}")
        else:
            print("❌ DeepSeek-R1-0528 model not found in configuration")
        
    except Exception as e:
        print(f"❌ Failed to load model configuration: {e}")
    
    print()


async def test_api_connection():
    """Test API connection to DeepSeek-R1-0528 (if API key is available)."""
    print("Testing API connection...")
    
    deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
    if not deepinfra_key:
        print("⚠️  DEEPINFRA_API_KEY not found - skipping API test")
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
        
        # Test with a simple prompt
        test_prompt = "Write a very brief story about a robot learning to paint. Keep it under 100 words."
        
        print(f"Sending test prompt to {config['model_name']}...")
        response = await evaluator.generate_response(test_prompt)
        
        print("✅ API connection successful!")
        print(f"Response length: {len(response)} characters")
        print("Response preview:")
        print("-" * 50)
        print(response[:200] + "..." if len(response) > 200 else response)
        print("-" * 50)
        
        # Check if thinking text was filtered out
        if '<think>' in response or '<thinking>' in response or '[Thinking]' in response:
            print("⚠️  Warning: Response may still contain thinking text")
        else:
            print("✅ No thinking text detected in response")
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("DeepSeek-R1-0528 Integration Test")
    print("=" * 50)
    
    test_thinking_filter()
    test_model_config()
    
    # Run async API test
    try:
        asyncio.run(test_api_connection())
    except Exception as e:
        print(f"Failed to run API test: {e}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()