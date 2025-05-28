"""
Unified Context System - Example Usage

This shows how the new unified system eliminates the need to manage
separate context limits and ensures truncation never happens silently.
"""

from storybench.unified_context_system import (
    create_32k_system,
    create_128k_system, 
    create_1m_system,
    ContextLimitExceededError
)

def basic_usage_example():
    """Basic usage with automatic limit inheritance."""
    
    # Create unified system - context manager and LLM share the same limit
    context_manager, llm = create_32k_system("/path/to/gemma-32k.gguf")
    
    # Both components now have the same 32K limit
    print(f"Context Manager Limit: {context_manager.get_max_context_tokens()}")
    print(f"LLM Context Size: {llm.n_ctx}")
    # Both will be 32000 - single source of truth!
    
    return context_manager, llm

def scaling_example():
    """How to scale from 32K to 128K to 1M - just change one function call."""
    
    # Start with 32K
    context_manager_32k, llm_32k = create_32k_system("/path/to/gemma-32k.gguf")
    
    # Scale to 128K - everything automatically adjusts
    context_manager_128k, llm_128k = create_128k_system("/path/to/gemma-128k.gguf")
    
    # Scale to 1M - still just one parameter change
    context_manager_1m, llm_1m = create_1m_system("/path/to/future-1m-model.gguf")
    
    print("Scaling demonstration:")
    print(f"32K System: {context_manager_32k.get_max_context_tokens()} tokens")
    print(f"128K System: {context_manager_128k.get_max_context_tokens()} tokens") 
    print(f"1M System: {context_manager_1m.get_max_context_tokens()} tokens")

if __name__ == "__main__":
    print("Unified Context System Examples")
    print("=" * 40)
    print("To test with real models, update the model paths and run the functions")
