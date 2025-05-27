#!/usr/bin/env python3
"""
Deep investigation of low token count failures.
Testing various hypotheses for why 867 tokens causes failures.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any

# Setup path
sys.path.append('src')

from storybench.evaluators.local_evaluator import LocalEvaluator

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def investigate_failure_cause():
    """Investigate why failures occur at low token counts."""
    
    # Load local model config
    with open('config/local_models.json', 'r') as f:
        local_config = json.load(f)
    
    model_config = local_config['models'][0]
    
    # Transform config
    evaluator_config = {
        "type": model_config.get("type"),
        "provider": model_config.get("provider"),
        "repo_id": model_config.get("model_repo_id"),
        "filename": model_config.get("model_filename"),
        "subdirectory": model_config.get("subdirectory"),
    }
    evaluator_config.update(model_config.get("model_settings", {}))
    
    print(f"=== INVESTIGATION: Low Token Count Failures ===")
    print(f"Model: {model_config['name']}")
    print(f"Context window: {evaluator_config.get('n_ctx', 'unknown')}")
    print(f"Max tokens: {evaluator_config.get('max_tokens', 'unknown')}")
    
    evaluator = LocalEvaluator(model_config['name'], evaluator_config)
    
    print("\n--- Setting up model ---")
    success = await evaluator.setup()
    if not success:
        print("❌ Setup failed")
        return
    
    # Test 1: Simple prompts at various lengths
    print(f"\n=== TEST 1: Token Length Analysis ===")
    
    test_cases = [
        ("Very Short", "Write a story.", 50),
        ("Short", "Write a short story about a detective investigating a mysterious case.", 200),
        ("Medium", "Write a detailed story about a detective investigating a mysterious case. Include dialogue, setting descriptions, and character development." * 2, 500),
        ("Problem Length", "Write a detailed story about a detective investigating a mysterious case. Include dialogue, setting descriptions, and character development." * 4, 867),  # This should trigger the issue
        ("Longer", "Write a detailed story about a detective investigating a mysterious case. Include dialogue, setting descriptions, and character development." * 8, 1500)
    ]
    
    for test_name, prompt, expected_tokens in test_cases:
        actual_tokens = len(prompt) // 3
        print(f"\n--- {test_name} Test ---")
        print(f"Expected ~{expected_tokens} tokens, actual ~{actual_tokens} tokens")
        print(f"Prompt length: {len(prompt)} chars")
        
        try:
            response = await evaluator.generate_response(prompt, max_tokens=1000, temperature=0.7)
            if response and response.get('text') and len(response['text']) > 50:
                print(f"✅ SUCCESS: {len(response['text'])} chars, {response.get('completion_tokens', 0)} tokens")
            else:
                print(f"❌ FAILURE: {len(response.get('text', '')) if response else 0} chars")
                print(f"   Response: {response}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    # Test 2: Context building patterns (the real issue might be here)
    print(f"\n=== TEST 2: Context Building Pattern Analysis ===")
    
    simulated_context = ""
    context_prompts = [
        "Write a story about a detective.",
        "Continue the story by adding a mysterious clue.", 
        "Add a plot twist to the detective story.",
    ]
    
    for i, prompt in enumerate(context_prompts):
        print(f"\n--- Context Step {i+1} ---")
        
        # Build context like run_end_to_end.py does
        if simulated_context:
            combined_prompt = simulated_context + "\n\n---\n\n" + prompt
        else:
            combined_prompt = prompt
            
        context_tokens = len(combined_prompt) // 3
        print(f"Context length: {len(simulated_context)} chars")
        print(f"Combined prompt: {len(combined_prompt)} chars (~{context_tokens} tokens)")
        
        try:
            response = await evaluator.generate_response(combined_prompt)
            if response and response.get('text') and len(response['text']) > 50:
                print(f"✅ SUCCESS: {len(response['text'])} chars")
                # Simulate adding to context
                simulated_context += response['text'] + "\n\n"
            else:
                print(f"❌ FAILURE: {len(response.get('text', '')) if response else 0} chars")
                print(f"   This is where the pattern breaks!")
                break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            break
    
    # Test 3: Model parameter investigation
    print(f"\n=== TEST 3: Parameter Sensitivity ===")
    
    problematic_prompt = "Write a detailed story about a detective investigating a mysterious case. Include dialogue, setting descriptions, and character development." * 4
    
    parameter_tests = [
        {"temperature": 0.1, "max_tokens": 500},
        {"temperature": 0.5, "max_tokens": 500},
        {"temperature": 0.8, "max_tokens": 500},
        {"temperature": 0.7, "max_tokens": 100},
        {"temperature": 0.7, "max_tokens": 2000},
        {"temperature": 0.7, "max_tokens": 500, "top_p": 0.5},
        {"temperature": 0.7, "max_tokens": 500, "top_k": 20},
    ]
    
    for params in parameter_tests:
        print(f"\n--- Testing params: {params} ---")
        try:
            response = await evaluator.generate_response(problematic_prompt, **params)
            if response and response.get('text') and len(response['text']) > 50:
                print(f"✅ SUCCESS with these params: {len(response['text'])} chars")
            else:
                print(f"❌ STILL FAILS with these params")
        except Exception as e:
            print(f"❌ ERROR with these params: {e}")
    
    # Test 4: Memory and resource check
    print(f"\n=== TEST 4: Resource Analysis ===")
    try:
        import psutil
        import torch
        
        # CPU and RAM
        print(f"CPU usage: {psutil.cpu_percent()}%")
        print(f"RAM usage: {psutil.virtual_memory().percent}%")
        print(f"Available RAM: {psutil.virtual_memory().available // (1024**3)} GB")
        
        # GPU
        if torch.cuda.is_available():
            print(f"GPU memory allocated: {torch.cuda.memory_allocated() // (1024**2)} MB")
            print(f"GPU memory reserved: {torch.cuda.memory_reserved() // (1024**2)} MB")
            print(f"GPU memory free: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved()) // (1024**2)} MB")
        
    except ImportError:
        print("psutil not available for resource monitoring")
    
    await evaluator.cleanup()

if __name__ == "__main__":
    asyncio.run(investigate_failure_cause())
