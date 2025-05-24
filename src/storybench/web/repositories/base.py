"""Abstract repository interface for data access."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class Repository(ABC):
    """Abstract repository interface for data persistence."""

    @abstractmethod
    async def load_models_config(self) -> Dict[str, Any]:
        """Load models configuration."""
        pass

    @abstractmethod
    async def save_models_config(self, config: Dict[str, Any]) -> None:
        """Save models configuration."""
        pass

    @abstractmethod
    async def load_prompts(self) -> Dict[str, List[Dict[str, str]]]:
        """Load prompts configuration."""
        pass

    @abstractmethod
    async def save_prompts(self, prompts: Dict[str, List[Dict[str, str]]]) -> None:
        """Save prompts configuration."""
        pass

    @abstractmethod
    async def load_evaluation_criteria(self) -> Dict[str, Any]:
        """Load evaluation criteria."""
        pass

    @abstractmethod
    async def save_evaluation_criteria(self, criteria: Dict[str, Any]) -> None:
        """Save evaluation criteria."""
        pass


    @abstractmethod
    async def load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys from environment."""
        pass

    @abstractmethod
    async def save_api_keys(self, keys: Dict[str, Optional[str]]) -> None:
        """Save API keys to environment file."""
        pass

    @abstractmethod
    async def load_results(self, model_name: Optional[str] = None, 
                          config_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load evaluation results."""
        pass

    @abstractmethod
    async def save_result(self, model_name: str, result_data: Dict[str, Any]) -> None:
        """Save individual evaluation result."""
        pass

    @abstractmethod
    async def get_result_versions(self) -> List[str]:
        """Get list of available result configuration versions."""
        pass
