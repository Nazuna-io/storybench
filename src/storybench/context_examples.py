"""Example configurations for different context sizes and overflow handling."""

from storybench.robust_context_manager import (
    create_32k_context_manager, 
    create_128k_context_manager,
    create_1m_context_manager,
    OverflowStrategy
)
from storybench.langchain_llm_wrapper import create_langchain_llm

# Example 1: Current 32K Gemma 3 setup
def setup_32k_model():
    """Setup for current 32K Gemma 3 model."""
    # Context manager with auto-truncation on overflow
    context_manager = create_32k_context_manager(
        overflow_strategy=OverflowStrategy.AUTO_TRUNCATE
    )
    
    # LLM wrapper matching context size
    llm = create_langchain_llm(
        model_path="/path/to/gemma-3-32k.gguf",
        model_name="Gemma-3-32K",
        context_size=32768,  # Match model capacity
        n_batch=512
    )
    
    return context_manager, llm

# Example 2: Upgrading to 128K model
def setup_128k_model():
    """Setup for 128K Gemma 3 or similar model."""
    # Just change the context size - everything else scales
    context_manager = create_128k_context_manager(
        overflow_strategy=OverflowStrategy.CHUNK_PROCESS  # Different strategy for large contexts
    )
    
    llm = create_langchain_llm(
        model_path="/path/to/gemma-3-128k.gguf",
        model_name="Gemma-3-128K", 
        context_size=131072,  # 128K tokens
        n_batch=1024,  # Larger batch for efficiency
        n_threads=8    # More threads for larger model
    )
    
    return context_manager, llm

# Example 3: Future 1M+ context models
def setup_1m_model():
    """Setup for future 1M+ context models."""
    context_manager = create_1m_context_manager(
        overflow_strategy=OverflowStrategy.COMPRESS  # Use compression for massive contexts
    )
    
    llm = create_langchain_llm(
        model_path="/path/to/future-large-model.gguf",
        model_name="Future-Large-Model",
        context_size=1048576,  # 1M tokens
        n_batch=2048,
        n_threads=16
    )
    
    return context_manager, llm

# Example usage in evaluation
def safe_evaluation_example():
    """Example of safe evaluation with overflow handling."""
    
    # Setup (choose based on your model)
    context_manager, llm = setup_32k_model()  # or setup_128k_model()
    
    # Prepare context with overflow protection
    result = context_manager.build_context_safe(
        history_text=very_long_history,
        current_prompt=current_evaluation_prompt
    )
    
    # Check the result
    if result["status"] == "success":
        # Context fits perfectly
        response = llm(result["context"])
        
    elif result["status"] == "overflow_truncated":
        # Context was truncated but evaluation can proceed
        print(f"Warning: Context truncated to {result['tokens_used']} tokens")
        response = llm(result["context"])
        
    elif result["status"] == "overflow_chunked":
        # Process in chunks
        responses = []
        for chunk in result["chunks"]:
            chunk_response = llm(chunk)
            responses.append(chunk_response)
        # Combine responses as needed
        
    elif result["status"] == "overflow_error":
        # Handle gracefully
        print(f"Error: {result['error']}")
        # Use fallback evaluation or skip
        
    return response
