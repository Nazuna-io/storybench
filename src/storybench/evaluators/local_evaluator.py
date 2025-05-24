"""Local GGUF model evaluator using llama-cpp-python."""

from typing import Dict, Any
from .base import BaseEvaluator


class LocalEvaluator(BaseEvaluator):
    """Evaluator for local GGUF models (placeholder for future implementation)."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize local evaluator."""
        super().__init__(name, config)
        
    async def setup(self) -> bool:
        """Setup local model (not implemented yet)."""
        print(f"Local model evaluation not yet implemented for {self.name}")
        return False
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using local model (not implemented yet)."""
        raise NotImplementedError("Local model evaluation not yet implemented")
        
    async def cleanup(self) -> None:
        """Clean up local model resources (not implemented yet)."""
        pass
