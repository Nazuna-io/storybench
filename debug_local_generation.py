#!/usr/bin/env python3
"""
Debug script to test local model generation and identify empty response issues.
"""

import asyncio
import json
import os
import logging
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Setup path
sys.path.append('src')

from storybench.evaluators.local_evaluator import LocalEvaluator

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_local_model():
    """Test local model generation with various prompts."""
    
    load_dotenv()
    
    # Load local model config
    with open('config/local_models.json', 'r') as f:
        local_config = json.load(f)
    
    model_config = local_config['models'][0]  # Get first model
    
    print(f"Testing model: {model_config['name']}")
    print(f"Config: {json.dumps(model_config, indent=2)}")
    
    # Transform config to match what LocalEvaluator expects
    evaluator_config = {
        "type": model_config.get("type"),
        "provider": model_config.get("provider"),
        "repo_id": model_config.get("model_repo_id"),  # Transform key
        "filename": model_config.get("model_filename"),  # Transform key
        "subdirectory": model_config.get("subdirectory"),
        "model_settings": model_config.get("model_settings", {})
    }
    
    # Add model_settings to the config (flattened format for LocalEvaluator)
    evaluator_config.update(model_config.get("model_settings", {}))
    
    print(f"\nTransformed config for evaluator: {json.dumps(evaluator_config, indent=2)}")
    
    # Create evaluator
    evaluator = LocalEvaluator(model_config['name'], evaluator_config)
    
    # Setup model
    print("\n--- Setting up model ---")
    success = await evaluator.setup()
    if not success:
        print("❌ Model setup failed!")
        return
    
    print("✅ Model setup successful!")
    
    # Test with various prompts of increasing complexity
    test_prompts = [
        # Simple prompt
        {
            "name": "Simple",
            "text": "Write a short sentence about a cat."
        },
        # Medium prompt
        {
            "name": "Medium", 
            "text": "Write a brief story about a detective solving a mystery. Include dialogue and action."
        },
        # Complex prompt (similar to what's causing issues)
        {
            "name": "Complex Narrative",
            "text": """Write a compelling narrative scene that demonstrates strong character development. Focus on:

1. A protagonist facing a meaningful internal conflict
2. Vivid sensory details that immerse the reader
3. Natural dialogue that reveals character traits
4. A moment of realization or growth
5. Rich emotional depth

Show don't tell - let the character's actions and words reveal their inner state. Aim for 300-500 words."""
        },
        # Very long context test
        {
            "name": "Long Context",
            "text": """You are writing a continuation of a story. Here is the previous context:

[Previous scene content would go here - this is a placeholder for a very long context that might cause issues]

The protagonist has been through multiple challenges, faced several conflicts, and is now approaching the climax of their journey. The setting is richly detailed, with multiple characters having been introduced and developed throughout the narrative.

Now continue the story with a pivotal scene that brings resolution to the main conflict while maintaining the established tone and character voices. Include dialogue, action, and internal reflection. The scene should be approximately 400-600 words and feel like a natural continuation of what came before."""
        }
    ]
    
    # Test each prompt
    for i, prompt_data in enumerate(test_prompts):
        print(f"\n--- Test {i+1}: {prompt_data['name']} ---")
        print(f"Prompt length: {len(prompt_data['text'])} characters")
        
        try:
            # Test with default settings
            print("Generating response...")
            response = await evaluator.generate_response(prompt_data['text'])
            
            if response and 'text' in response and response['text']:
                generated_text = response['text'].strip()
                print(f"✅ Success! Generated {len(generated_text)} characters")
                print(f"Generation time: {response.get('generation_time', 0):.2f}s")
                print(f"Tokens/sec: {response.get('tokens_per_second', 0):.1f}")
                print(f"Response preview: {generated_text[:200]}...")
                
                # Check for quality indicators
                if len(generated_text) < 50:
                    print("⚠️ Warning: Response is very short")
                if not any(char.isalpha() for char in generated_text):
                    print("⚠️ Warning: Response contains no alphabetic characters")
                    
            else:
                print("❌ Empty or invalid response!")
                print(f"Response object: {response}")
                
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            import traceback
            traceback.print_exc()
        
        # Add a small delay between tests
        await asyncio.sleep(1)
    
    # Test with different temperature settings
    print(f"\n--- Temperature Test ---")
    simple_prompt = "Write a one sentence story."
    
    for temp in [0.1, 0.5, 0.8, 1.0]:
        print(f"\nTesting temperature {temp}:")
        try:
            response = await evaluator.generate_response(simple_prompt, temperature=temp)
            if response and response.get('text'):
                print(f"✅ Success: {len(response['text'])} chars")
                print(f"Preview: {response['text'][:100]}...")
            else:
                print("❌ Empty response")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Cleanup
    print(f"\n--- Cleanup ---")
    await evaluator.cleanup()
    print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_local_model())
