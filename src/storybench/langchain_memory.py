"""LangChain memory module for Storybench context management."""

import logging
from typing import Dict, Any, List, Optional

try:
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain_core.memory import BaseMemory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
except ImportError:
    raise ImportError(
        "LangChain packages not found. Please install: "
        "pip install langchain langchain-core"
    )

logger = logging.getLogger(__name__)


class StorybenchMemory:
    """
    Memory management for Storybench using LangChain components.
    
    Handles conversation history and context across multi-prompt sequences
    for large context scenarios without truncation.
    """
    
    def __init__(
        self,
        memory_type: str = "buffer",
        max_token_limit: Optional[int] = None,
        return_messages: bool = True
    ):
        """Initialize Storybench memory.
        
        Args:
            memory_type: Type of memory ("buffer" or "summary")
            max_token_limit: Optional token limit for memory
            return_messages: Whether to return messages or string
        """
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit
        self.return_messages = return_messages
        
        # Initialize the appropriate LangChain memory
        if memory_type == "buffer":
            self.memory = ConversationBufferMemory(
                return_messages=return_messages,
                memory_key="history"
            )
        elif memory_type == "summary":
            # Note: This would require an LLM for summarization
            # For now, we'll use buffer memory
            logger.warning("Summary memory not fully implemented, using buffer memory")
            self.memory = ConversationBufferMemory(
                return_messages=return_messages,
                memory_key="history"
            )
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        logger.info(f"Initialized {memory_type} memory with return_messages={return_messages}")
    
    def add_interaction(self, human_input: str, ai_response: str):
        """Add a human-AI interaction to memory.
        
        Args:
            human_input: The human/user input
            ai_response: The AI response
        """
        self.memory.save_context(
            {"input": human_input},
            {"output": ai_response}
        )
        logger.debug(f"Added interaction to memory: {len(human_input)} + {len(ai_response)} chars")
    
    def get_context(self) -> str:
        """Get the current context from memory as a string.
        
        Returns:
            Memory context as formatted string
        """
        memory_variables = self.memory.load_memory_variables({})
        
        if self.return_messages:
            # Convert messages to string format
            messages = memory_variables.get("history", [])
            context_parts = []
            
            for message in messages:
                if isinstance(message, HumanMessage):
                    context_parts.append(f"Human: {message.content}")
                elif isinstance(message, AIMessage):
                    context_parts.append(f"AI: {message.content}")
                else:
                    context_parts.append(f"Message: {message.content}")
            
            return "\n\n".join(context_parts)
        else:
            # Already a string
            return memory_variables.get("history", "")
    
    def get_messages(self) -> List[BaseMessage]:
        """Get the current context as LangChain messages.
        
        Returns:
            List of LangChain message objects
        """
        if not self.return_messages:
            logger.warning("Memory configured for string output, not messages")
            return []
        
        memory_variables = self.memory.load_memory_variables({})
        return memory_variables.get("history", [])
    
    def clear(self):
        """Clear all memory."""
        self.memory.clear()
        logger.debug("Memory cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current memory state.
        
        Returns:
            Dictionary with memory statistics
        """
        context = self.get_context()
        messages = self.get_messages() if self.return_messages else []
        
        return {
            "memory_type": self.memory_type,
            "context_length": len(context),
            "estimated_tokens": len(context) // 3.5,  # Rough estimate
            "message_count": len(messages),
            "max_token_limit": self.max_token_limit,
            "return_messages": self.return_messages
        }


class StorybenchConversationManager:
    """
    High-level conversation manager combining memory and context management.
    
    Integrates LangChain memory with Storybench context management for
    seamless large context handling.
    """
    
    def __init__(
        self,
        memory_type: str = "buffer",
        max_context_tokens: int = 32000
    ):
        """Initialize conversation manager.
        
        Args:
            memory_type: Type of memory to use
            max_context_tokens: Maximum context tokens
        """
        self.memory = StorybenchMemory(memory_type=memory_type)
        self.max_context_tokens = max_context_tokens
        
        logger.info(f"Initialized conversation manager with {max_context_tokens} max tokens")
    
    def add_exchange(self, prompt: str, response: str):
        """Add a prompt/response exchange to the conversation.
        
        Args:
            prompt: The user prompt
            response: The AI response
        """
        self.memory.add_interaction(prompt, response)
    
    def get_conversation_context(self) -> str:
        """Get the full conversation context as a formatted string.
        
        Returns:
            Complete conversation context
        """
        return self.memory.get_context()
    
    def prepare_prompt_with_context(self, new_prompt: str) -> str:
        """Prepare a new prompt with full conversation context.
        
        Args:
            new_prompt: The new prompt to add
            
        Returns:
            Complete prompt with conversation history
        """
        context = self.get_conversation_context()
        
        if context:
            return f"{context}\n\nHuman: {new_prompt}"
        else:
            return f"Human: {new_prompt}"
    
    def clear_conversation(self):
        """Clear the entire conversation history."""
        self.memory.clear()
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get comprehensive conversation statistics.
        
        Returns:
            Dictionary with conversation statistics
        """
        memory_stats = self.memory.get_stats()
        context = self.get_conversation_context()
        
        return {
            **memory_stats,
            "total_context_tokens": len(context) // 3.5,
            "max_context_tokens": self.max_context_tokens,
            "context_utilization": (len(context) // 3.5) / self.max_context_tokens
        }


# Convenience functions
def create_storybench_memory(memory_type: str = "buffer") -> StorybenchMemory:
    """Create a Storybench memory instance.
    
    Args:
        memory_type: Type of memory ("buffer" or "summary")
        
    Returns:
        Configured StorybenchMemory instance
    """
    return StorybenchMemory(memory_type=memory_type)


def create_conversation_manager(max_tokens: int = 32000) -> StorybenchConversationManager:
    """Create a conversation manager for large contexts.
    
    Args:
        max_tokens: Maximum context tokens
        
    Returns:
        Configured conversation manager
    """
    return StorybenchConversationManager(max_context_tokens=max_tokens)
