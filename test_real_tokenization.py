#!/usr/bin/env python3
"""Test script for real tokenization with LocalEvaluator."""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.evaluators.local_evaluator import LocalEvaluator
from storybench.context_manager import build_context_token_aware


class TokenizerAdapter:
    """Adapter to make LocalEvaluator compatible with context manager."""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
    
    def tokenize(self, text: bytes, add_bos: bool = True, special: bool = False) -> list:
        # Convert bytes to string and use evaluator's tokenize method
        text_str = text.decode('utf-8')
        return self.evaluator.tokenize_text(text_str, add_bos=add_bos)
    
    def detokenize(self, tokens: list) -> bytes:
        # Use evaluator's detokenize method and convert to bytes
        text_str = self.evaluator.detokenize_tokens(tokens)
        return text_str.encode('utf-8')


async def test_real_tokenization():
    """Test tokenization with a real model."""
    print("=== Testing Real Tokenization ===")
    
    # Configure for the available model
    config = {
        "repo_id": "unsloth/gemma-3-1b-it-GGUF",
        "filename": "gemma-3-1b-it-Q2_K_L.gguf",
        "model_settings": {
            "n_ctx": 8192,
            "max_tokens": 2048,
            "temperature": 0.8,
            "n_gpu_layers": 0  # Use CPU for this test
        }
    }
    
    # Create and setup evaluator
    evaluator = LocalEvaluator("test-gemma", config)    
    print("Setting up model...")
    try:
        success = await evaluator.setup()
        if not success:
            print("FAIL: Model setup failed")
            return
        print("✓ Model loaded successfully")
        
        # Test basic tokenization
        test_text = "Hello, this is a test sentence."
        tokens = evaluator.tokenize_text(test_text)
        reconstructed = evaluator.detokenize_tokens(tokens)
        
        print(f"Original text: '{test_text}'")
        print(f"Token count: {len(tokens)}")
        print(f"Reconstructed: '{reconstructed}'")
        print(f"Round-trip test: {'PASS' if test_text.strip() in reconstructed else 'FAIL'}")
        
        # Test available context calculation
        available_tokens = evaluator.get_available_context_tokens()
        print(f"Available context tokens: {available_tokens}")
        
        # Test context building with real tokenizer
        print("\n=== Testing Context Building ===")
        
        # Create tokenizer adapter
        tokenizer = TokenizerAdapter(evaluator)
        
        # Test cases
        short_history = "This is a short history."
        long_history = "This is a longer history. " * 100  # ~2500 chars
        prompt = "What happens next in the story?"
        
        # Test 1: Short history should not truncate
        result1 = build_context_token_aware(short_history, prompt, available_tokens, tokenizer)
        print(f"Test 1 - Short history:")
        print(f"  Input: {len(short_history)} chars")
        print(f"  Output: {len(result1)} chars")
        print(f"  Truncated: {'YES' if 'truncated' in result1 else 'NO'}")
        
        # Test 2: Long history might truncate depending on available tokens
        result2 = build_context_token_aware(long_history, prompt, available_tokens, tokenizer)
        print(f"Test 2 - Long history:")
        print(f"  Input: {len(long_history)} chars")
        print(f"  Output: {len(result2)} chars")
        print(f"  Truncated: {'YES' if 'truncated' in result2 else 'NO'}")
        
        # Test 3: Very constrained token budget
        constrained_tokens = 100  # Very small
        result3 = build_context_token_aware(long_history, prompt, constrained_tokens, tokenizer)
        print(f"Test 3 - Constrained tokens ({constrained_tokens}):")
        print(f"  Input: {len(long_history)} chars")
        print(f"  Output: {len(result3)} chars")
        print(f"  Truncated: {'YES' if 'truncated' in result3 else 'NO'}")
        
    except Exception as e:
        print(f"FAIL: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await evaluator.cleanup()
        print("✓ Cleanup completed")


if __name__ == "__main__":
    asyncio.run(test_real_tokenization())
