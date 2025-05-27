#!/usr/bin/env python3
"""
Test the specific context concatenation hypothesis.
"""

import asyncio
import json
import sys

sys.path.append('src')
from storybench.evaluators.local_evaluator import LocalEvaluator

async def test_concatenation_hypothesis():
    """Test if the context concatenation pattern is causing issues."""
    
    # Setup model
    with open('config/local_models.json', 'r') as f:
        local_config = json.load(f)
    
    model_config = local_config['models'][0]
    evaluator_config = {
        "type": model_config.get("type"),
        "provider": model_config.get("provider"),
        "repo_id": model_config.get("model_repo_id"),
        "filename": model_config.get("model_filename"),
        "subdirectory": model_config.get("subdirectory"),
    }
    evaluator_config.update(model_config.get("model_settings", {}))
    
    evaluator = LocalEvaluator(model_config['name'], evaluator_config)
    await evaluator.setup()
    
    print("=== TESTING CONCATENATION HYPOTHESIS ===")
    
    # Generate first response
    print("\n1. Generate first response...")
    response1 = await evaluator.generate_response("Write a short story about a detective.")
    if not response1 or not response1.get('text'):
        print("❌ First response failed")
        return
    
    story_part1 = response1['text']
    print(f"✅ First response: {len(story_part1)} chars")
    
    # Test different concatenation methods
    next_prompt = "Continue the story by adding a mysterious clue."
    
    concatenation_tests = [
        ("Original Method", story_part1 + "\n\n---\n\n" + next_prompt),
        ("Simple Newlines", story_part1 + "\n\n" + next_prompt),
        ("Single Newline", story_part1 + "\n" + next_prompt),
        ("Space Separator", story_part1 + " " + next_prompt),
        ("Clean Break", f"Previous story:\n{story_part1}\n\nNew instruction: {next_prompt}"),
        ("Gemma Format", f"{story_part1}\n\n### Instruction:\n{next_prompt}\n\n### Response:\n"),
    ]
    
    for method_name, combined_prompt in concatenation_tests:
        print(f"\n--- Testing: {method_name} ---")
        print(f"Combined length: {len(combined_prompt)} chars (~{len(combined_prompt)//3} tokens)")
        
        try:
            response = await evaluator.generate_response(combined_prompt, max_tokens=500)
            if response and response.get('text') and len(response['text']) > 50:
                print(f"✅ SUCCESS: {len(response['text'])} chars")
            else:
                print(f"❌ FAILED: {len(response.get('text', '')) if response else 0} chars")
                print("   ^^ This method causes the issue!")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    await evaluator.cleanup()

if __name__ == "__main__":
    asyncio.run(test_concatenation_hypothesis())
