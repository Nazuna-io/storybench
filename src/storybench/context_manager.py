"""Token-aware context management for local GGUF models."""

import logging
from typing import List, Optional, Protocol

logger = logging.getLogger(__name__)


class TokenizerProtocol(Protocol):
    """Protocol for tokenizer interface."""
    
    def tokenize(self, text: bytes, add_bos: bool = True, special: bool = False) -> List[int]:
        """Tokenize text into token IDs."""
        ...
    
    def detokenize(self, tokens: List[int]) -> bytes:
        """Convert token IDs back to text."""
        ...


def build_context_token_aware(
    full_sequence_text: str,
    current_prompt_text: str,
    available_input_tokens: int,
    tokenizer: TokenizerProtocol
) -> str:
    """
    Build context for the LLM, respecting token limits and prioritizing recent history.
    
    Args:
        full_sequence_text: The accumulated text of previous responses in the sequence.
        current_prompt_text: The text of the current prompt.
        available_input_tokens: The number of tokens available for the input context.
        tokenizer: A tokenizer object with tokenize() and detokenize() methods.
        
    Returns:
        The final context string to send to the model.
    """
    history_prompt_separator = "\n\n---\n\n"
    
    # Handle empty history case
    if not full_sequence_text:
        return current_prompt_text
    
    try:
        # Tokenize current prompt and separator to determine their token cost
        current_prompt_tokens = tokenizer.tokenize(current_prompt_text.encode('utf-8'), add_bos=False)
        separator_tokens = tokenizer.tokenize(history_prompt_separator.encode('utf-8'), add_bos=False)
        
        # Calculate tokens available for the historical text
        # Small buffer for potential tokenization differences
        tokens_for_history = available_input_tokens - len(current_prompt_tokens) - len(separator_tokens) - 50        
        # Ensure tokens_for_history is not negative
        if tokens_for_history <= 0:
            logger.warning(f"Prompt too long ({len(current_prompt_tokens)} tokens), using prompt only")
            return current_prompt_text
        
        # Tokenize the full sequence text
        history_tokens = tokenizer.tokenize(full_sequence_text.encode('utf-8'), add_bos=False)
        
        # Check if we need to truncate
        if len(history_tokens) <= tokens_for_history:
            # History fits entirely - no truncation needed
            logger.debug(f"Full history fits: {len(history_tokens)} tokens <= {tokens_for_history} available")
            return f"{full_sequence_text}{history_prompt_separator}{current_prompt_text}"
        
        # Need to truncate - keep the most recent tokens
        logger.info(f"Truncating history: {len(history_tokens)} -> {tokens_for_history} tokens")
        truncated_history_tokens = history_tokens[-tokens_for_history:]
        
        # Convert back to text
        truncated_history_bytes = tokenizer.detokenize(truncated_history_tokens)
        truncated_history_text = truncated_history_bytes.decode('utf-8', errors='replace')
        
        # Optional: Clean up truncation point if it's mid-sentence
        # Look for natural boundaries near the start of truncated text
        truncation_cleaned = False
        for boundary in ['\n\n', '. ', '! ', '? ', '\n', ' ']:
            boundary_pos = truncated_history_text.find(boundary)
            if 0 < boundary_pos < 200:  # Look within first 200 characters
                truncated_history_text = truncated_history_text[boundary_pos + len(boundary):]
                truncation_cleaned = True
                logger.debug(f"Cleaned truncation at boundary: '{boundary}'")
                break        
        # Build final context with truncation indicator
        truncation_msg = "[...context truncated - showing recent content...]\n\n"
        final_context = f"{truncation_msg}{truncated_history_text}{history_prompt_separator}{current_prompt_text}"
        
        # Log the results
        original_chars = len(full_sequence_text)
        truncated_chars = len(truncated_history_text)
        final_tokens_estimate = len(tokenizer.tokenize(final_context.encode('utf-8'), add_bos=False))
        
        logger.info(f"Context truncation complete: {original_chars} -> {truncated_chars} chars "
                   f"(~{final_tokens_estimate} tokens, target: {available_input_tokens})")
        
        return final_context
        
    except Exception as e:
        logger.error(f"Token-aware context building failed: {e}")
        logger.info("Falling back to character-based truncation")
        
        # Fallback to character-based approach
        return _fallback_character_truncation(
            full_sequence_text, current_prompt_text, available_input_tokens
        )


def _fallback_character_truncation(
    full_sequence_text: str,
    current_prompt_text: str,
    available_input_tokens: int
) -> str:
    """
    Fallback character-based truncation when tokenization fails.
    
    Uses the existing logic as a safety net.
    """
    history_prompt_separator = "\n\n---\n\n"
    
    # Conservative character-to-token estimation (3 chars per token)
    max_chars = available_input_tokens * 3
    prompt_chars = len(current_prompt_text)
    separator_chars = len(history_prompt_separator)
    
    # Leave room for history
    available_for_history = max_chars - prompt_chars - separator_chars - 200  # Extra buffer
    
    if available_for_history <= 0:
        logger.warning("Fallback: prompt too long, using prompt only")
        return current_prompt_text
    
    if len(full_sequence_text) <= available_for_history:
        return f"{full_sequence_text}{history_prompt_separator}{current_prompt_text}"    
    # Truncate to fit
    truncated_text = full_sequence_text[-available_for_history:]
    
    # Find natural boundary
    for boundary in ['\n\n', '. ', '! ', '? ', '\n']:
        boundary_pos = truncated_text.find(boundary)
        if 0 < boundary_pos < 500:
            truncated_text = truncated_text[boundary_pos + len(boundary):]
            break
    
    logger.info(f"Fallback truncation: {len(full_sequence_text)} -> {len(truncated_text)} chars")
    
    return f"[...context truncated - showing recent content...]\n\n{truncated_text}{history_prompt_separator}{current_prompt_text}"


# For backward compatibility and testing
def estimate_tokens_simple(text: str) -> int:
    """Simple character-based token estimation (3 chars ≈ 1 token)."""
    return len(text) // 3
