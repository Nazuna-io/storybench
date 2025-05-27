#!/usr/bin/env python3
"""
Debug sequence generation to identify empty response patterns.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Setup path
sys.path.append('src')

from storybench.database.services.config_service import ConfigService
from storybench.evaluators.local_evaluator import LocalEvaluator
from storybench.models.config import Config

async def test_sequence_generation():
    """Test sequence generation with actual prompts from database."""
    
    load_dotenv()
    
    # Connect to database
    mongodb_uri = os.getenv("MONGODB_URI")
    database_client = AsyncIOMotorClient(mongodb_uri)
    database = database_client["storybench"]
    
    try:
        # Get prompts from database
        config_service = ConfigService(database)
        prompts_config = await config_service.get_active_prompts()
        
        if not prompts_config or not hasattr(prompts_config, 'sequences'):
            print("❌ No prompts found in database")
            return
            
        sequences = prompts_config.sequences
        print(f"Found {len(sequences)} sequences")
        
        # Get first sequence with multiple prompts
        test_sequence = None
        for seq_name, prompts in sequences.items():
            if len(prompts) > 2:  # Find a sequence with multiple prompts
                test_sequence = (seq_name, prompts)
                break
        
        if not test_sequence:
            print("❌ No multi-prompt sequences found")
            return
            
        seq_name, prompts = test_sequence
        print(f"\nTesting sequence: {seq_name} with {len(prompts)} prompts")
        
        # Setup model
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
            "model_settings": model_config.get("model_settings", {})
        }
        evaluator_config.update(model_config.get("model_settings", {}))
        
        evaluator = LocalEvaluator(model_config['name'], evaluator_config)
        
        print("Setting up model...")
        success = await evaluator.setup()
        if not success:
            print("❌ Model setup failed")
            return
        
        # Test sequence generation (simulating how run_end_to_end.py works)
        print("\n=== Simulating Sequence Generation ===")
        full_sequence_text = ""  # This accumulates context
        
        for prompt_idx, prompt_obj in enumerate(prompts):
            # Handle both dict and object formats
            if hasattr(prompt_obj, 'text'):
                prompt_text = prompt_obj.text
                prompt_name = prompt_obj.name
            else:
                prompt_text = prompt_obj['text']
                prompt_name = prompt_obj['name']
            
            print(f"\n--- Prompt {prompt_idx + 1}/{len(prompts)}: {prompt_name} ---")
            print(f"Current context length: {len(full_sequence_text)} chars")
            print(f"Prompt length: {len(prompt_text)} chars")
            
            # Build combined context (this is the critical part)
            if full_sequence_text:
                # This mimics the context building in run_end_to_end.py
                combined_text = full_sequence_text + "\n\n---\n\n" + prompt_text
            else:
                combined_text = prompt_text
                
            total_input_length = len(combined_text)
            estimated_tokens = total_input_length // 3
            print(f"Total input length: {total_input_length} chars (~{estimated_tokens} tokens)")
            
            # Check if we're approaching context limits
            max_context = evaluator_config.get('n_ctx', 32768)
            max_gen_tokens = evaluator_config.get('max_tokens', 16384)
            available_tokens = max_context - max_gen_tokens - 500  # safety buffer
            
            if estimated_tokens > available_tokens:
                print(f"⚠️ WARNING: Input may exceed context limit!")
                print(f"  Estimated tokens: {estimated_tokens}")
                print(f"  Available tokens: {available_tokens}")
                
                # Apply truncation like in run_end_to_end.py
                if len(full_sequence_text) > 5000:
                    truncated_context = full_sequence_text[-3000:]
                    combined_text = f"[...context truncated...]\n\n{truncated_context}\n\n---\n\n{prompt_text}"
                    print(f"  Applied truncation: {len(combined_text)} chars")
            
            try:
                # Generate response
                print("Generating...")
                response = await evaluator.generate_response(combined_text)
                
                if response and response.get('text'):
                    generated_text = response['text'].strip()
                    print(f"✅ Success: {len(generated_text)} chars in {response.get('generation_time', 0):.2f}s")
                    print(f"Preview: {generated_text[:150]}...")
                    
                    # Add to context for next iteration
                    full_sequence_text += generated_text + "\n\n"
                    
                    # Check for signs of problems
                    if len(generated_text) < 50:
                        print("⚠️ WARNING: Very short response - potential issue!")
                    
                else:
                    print("❌ EMPTY RESPONSE!")
                    print(f"Response object: {response}")
                    
                    # This is the key issue - let's try to recover
                    print("Attempting model reset...")
                    try:
                        await evaluator.reset_model_state()
                        print("Model reset successful")
                    except Exception as reset_err:
                        print(f"Model reset failed: {reset_err}")
            
            except Exception as e:
                print(f"❌ Generation error: {e}")
                import traceback
                traceback.print_exc()
        
        # Cleanup
        await evaluator.cleanup()
        
    finally:
        database_client.close()

if __name__ == "__main__":
    asyncio.run(test_sequence_generation())
