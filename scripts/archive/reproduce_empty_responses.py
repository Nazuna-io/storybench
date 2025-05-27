#!/usr/bin/env python3
"""
Reproduce the empty response issue by simulating the exact sequence generation pattern.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any

# Setup path
sys.path.append('src')

from storybench.evaluators.local_evaluator import LocalEvaluator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def reproduce_empty_response_issue():
    """Reproduce the exact pattern that causes empty responses."""
    
    # Load local model config
    with open('config/local_models.json', 'r') as f:
        local_config = json.load(f)
    
    model_config = local_config['models'][0]
    
    # Transform config exactly like run_end_to_end.py does
    evaluator_config = {
        "type": model_config.get("type"),
        "provider": model_config.get("provider"),
        "repo_id": model_config.get("model_repo_id"),
        "filename": model_config.get("model_filename"),
        "subdirectory": model_config.get("subdirectory"),
    }
    
    # Add model_settings (flattened)
    if model_config.get("model_settings"):
        evaluator_config.update(model_config["model_settings"])
    
    print(f"Testing model: {model_config['name']}")
    
    evaluator = LocalEvaluator(model_config['name'], evaluator_config)
    
    print("Setting up model...")
    success = await evaluator.setup()
    if not success:
        print("❌ Model setup failed")
        return
    
    # Test with progressively building context (simulating sequence)
    test_prompts = [
        "Write a short story about a detective.",
        "Continue the story by adding a mysterious clue.",
        "Add a plot twist to the detective story.",
        "Bring the story to a dramatic conclusion.",
        "Write an epilogue for the detective story."
    ]
    
    full_sequence_text = ""  # This accumulates like in run_end_to_end.py
    
    for i, prompt_text in enumerate(test_prompts):
        print(f"\n=== Prompt {i+1}/5 ===")
        print(f"Context length: {len(full_sequence_text)} chars")
        
        # Build context exactly like run_end_to_end.py
        if full_sequence_text:
            # Check for truncation (>5000 chars)
            if len(full_sequence_text) > 5000:
                truncated_context = full_sequence_text[-3000:]
                # Find boundary
                for boundary in ['\n\n', '. ', '! ', '? ', '\n']:
                    boundary_pos = truncated_context.find(boundary)
                    if 0 < boundary_pos < 500:
                        truncated_context = truncated_context[boundary_pos + len(boundary):]
                        break
                combined_text = f"[...context truncated - showing recent content...]\n\n{truncated_context}\n\n---\n\n{prompt_text}"
                print(f"Applied truncation: {len(full_sequence_text)} -> {len(truncated_context)} chars")
            else:
                combined_text = full_sequence_text + "\n\n---\n\n" + prompt_text
        else:
            combined_text = prompt_text
        
        estimated_tokens = len(combined_text) // 3
        print(f"Input: ~{estimated_tokens} tokens")
        
        try:
            # Generate with the exact same parameters as run_end_to_end.py
            model_settings = model_config.get("model_settings", {})
            response_text = await evaluator.generate_response(combined_text, **model_settings)
            
            # Check the EXACT same condition as run_end_to_end.py
            if response_text and isinstance(response_text, dict) and 'text' in response_text and response_text['text']:
                generated_text_str = response_text['text']
                print(f"✅ Success: {len(generated_text_str)} chars")
                print(f"Preview: {generated_text_str[:100]}...")
                
                # Add to context exactly like run_end_to_end.py
                full_sequence_text += generated_text_str + "\n\n"
                
                # Reset after large responses like run_end_to_end.py
                if len(generated_text_str) > 5000 and hasattr(evaluator, 'reset_model_state'):
                    try:
                        await evaluator.reset_model_state()
                        print("Reset model state after large response")
                    except Exception as reset_error:
                        print(f"Failed to reset model state: {reset_error}")
                        
            else:
                print("❌ EMPTY RESPONSE!")
                print(f"Response type: {type(response_text)}")
                print(f"Response value: {response_text}")
                if isinstance(response_text, dict):
                    print(f"Response keys: {list(response_text.keys())}")
                    if 'text' in response_text:
                        print(f"Text value: '{response_text['text']}'")
                        print(f"Text type: {type(response_text['text'])}")
                        print(f"Text length: {len(response_text['text']) if response_text['text'] else 'None'}")
                
                # Try to recover
                print("Attempting recovery...")
                try:
                    await evaluator.reset_model_state()
                    print("Model reset successful, retrying...")
                    
                    # Retry with simpler prompt
                    simple_response = await evaluator.generate_response("Continue the story.", temperature=0.8)
                    if simple_response and simple_response.get('text'):
                        print(f"Recovery successful: {len(simple_response['text'])} chars")
                    else:
                        print("Recovery failed - still empty")
                except Exception as recovery_error:
                    print(f"Recovery attempt failed: {recovery_error}")
        
        except Exception as e:
            print(f"❌ Generation error: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    await evaluator.cleanup()

if __name__ == "__main__":
    asyncio.run(reproduce_empty_response_issue())
