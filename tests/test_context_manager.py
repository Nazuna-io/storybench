#!/usr/bin/env python3
"""Test script for token-aware context management."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.context_manager import build_context_token_aware, estimate_tokens_simple


class MockTokenizer:
    """Mock tokenizer for testing."""
    
    def tokenize(self, text: bytes, add_bos: bool = True, special: bool = False) -> list:
        """Mock tokenization - roughly 3 chars per token."""
        text_str = text.decode('utf-8')
        # Simple mock: split by spaces and punctuation, roughly 3 chars per token
        tokens = []
        token_id = 1
        i = 0
        while i < len(text_str):
            # Take about 3 characters per token
            token_text = text_str[i:i+3]
            if token_text.strip():  # Only count non-empty tokens
                tokens.append(token_id)
                token_id += 1
            i += 3
        return tokens
    
    def detokenize(self, tokens: list) -> bytes:
        """Mock detokenization."""
        # For testing, we'll use a simple approach
        # In practice, this would reconstruct the original text
        estimated_chars = len(tokens) * 3
        mock_text = "x" * estimated_chars  # Mock text of appropriate length
        return mock_text.encode('utf-8')


def test_basic_functionality():
    """Test basic context building functionality."""
    print("=== Test 1: Basic Functionality ===")
    
    tokenizer = MockTokenizer()
    
    # Test case 1: Small context that should fit
    history = "Previous response was short."
    prompt = "What happens next?"
    available_tokens = 1000
    
    result = build_context_token_aware(history, prompt, available_tokens, tokenizer)
    print(f"Small context test:")
    print(f"  Input: {len(history)} chars history, {len(prompt)} chars prompt")
    print(f"  Output: {len(result)} chars")
    print(f"  Expected: No truncation")
    print(f"  Result: {'PASS' if '---' in result and 'truncated' not in result else 'FAIL'}")
    print()


def test_truncation():
    """Test truncation functionality."""
    print("=== Test 2: Truncation ===")
    
    tokenizer = MockTokenizer()
    
    # Test case 2: Large context that should be truncated
    history = "This is a very long history. " * 200  # ~6000 chars
    prompt = "What happens next?"
    available_tokens = 50  # Very small context window
    
    result = build_context_token_aware(history, prompt, available_tokens, tokenizer)
    print(f"Large context test:")
    print(f"  Input: {len(history)} chars history, {len(prompt)} chars prompt")
    print(f"  Available tokens: {available_tokens}")
    print(f"  Output: {len(result)} chars")
    print(f"  Expected: Truncation should occur")
    print(f"  Result: {'PASS' if 'truncated' in result and len(result) < len(history) else 'FAIL'}")
    print()


def test_comparison_with_old_method():
    """Compare with the old character-based method."""
    print("=== Test 3: Comparison with Old Method ===")
    
    # Simulate the old method
    def old_method(full_sequence_text, prompt_text, available_tokens):
        if len(full_sequence_text) > 5000:  # Old hard-coded limit
            truncated = full_sequence_text[-3000:]  # Old hard-coded window
            return f"[...truncated...]\n\n{truncated}\n\n---\n\n{prompt_text}"
        else:
            return full_sequence_text + "\n\n---\n\n" + prompt_text
    
    # Test cases
    test_cases = [
        ("Short text" * 10, 100),      # Should not truncate in either method
        ("Medium text " * 100, 1000),   # Old method truncates, new method might not
        ("Long text " * 500, 200),      # Both should truncate, but differently
    ]
    
    tokenizer = MockTokenizer()
    
    for i, (history, available_tokens) in enumerate(test_cases, 1):
        prompt = "Test prompt"
        
        old_result = old_method(history, prompt, available_tokens)
        new_result = build_context_token_aware(history, prompt, available_tokens, tokenizer)
        
        print(f"  Case {i}: {len(history)} chars, {available_tokens} tokens available")
        print(f"    Old method: {len(old_result)} chars {'(truncated)' if 'truncated' in old_result else '(full)'}")
        print(f"    New method: {len(new_result)} chars {'(truncated)' if 'truncated' in new_result else '(full)'}")
        
        # Check if new method provides more context when possible
        if available_tokens > 200 and len(history) > 5000:
            improvement = len(new_result) > len(old_result)
            print(f"    Improvement: {'YES' if improvement else 'NO'}")
        print()


if __name__ == "__main__":
    print("Testing Token-Aware Context Management")
    print("=" * 50)
    
    test_basic_functionality()
    test_truncation()
    test_comparison_with_old_method()
    
    print("Tests completed. Check results above.")
