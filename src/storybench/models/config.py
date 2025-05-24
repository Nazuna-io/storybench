"""Configuration management for storybench."""

import yaml
import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class GlobalSettings:
    """Global evaluation settings."""
    temperature: float = 0.9
    max_tokens: int = 4096
    num_runs: int = 3
    vram_limit_percent: int = 80


@dataclass
class ModelConfig:
    """Individual model configuration."""
    name: str
    type: str
    provider: str
    model_name: str
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    subdirectory: Optional[str] = None


@dataclass
class EvaluationConfig:
    """Evaluation settings."""
    auto_evaluate: bool = True
    evaluator_models: List[str] = None
    max_retries: int = 5
    
    def __post_init__(self):
        if self.evaluator_models is None:
            self.evaluator_models = ["claude-3-sonnet", "gemini-pro"]


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: str):
        """Initialize configuration from file path."""
        self.config_path = Path(config_path)
        self.version: int = 1
        self.global_settings: GlobalSettings = GlobalSettings()
        self.models: List[ModelConfig] = []
        self.evaluation: EvaluationConfig = EvaluationConfig()
        self.prompts: Dict[str, List[Dict[str, str]]] = {}
        self.evaluation_criteria: Dict[str, Any] = {}
        
    @classmethod
    def load_config(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        config = cls(config_path)
        config._load_models_config()
        config._load_prompts()
        config._load_evaluation_criteria()
        return config
        
    def _load_models_config(self) -> None:
        """Load models configuration from YAML."""
        models_path = self.config_path.parent / "models.yaml"
        with open(models_path, 'r') as f:
            data = yaml.safe_load(f)
            
        self.version = data.get("version", 1)
        
        # Load global settings
        global_data = data.get("global_settings", {})
        self.global_settings = GlobalSettings(**global_data)
        
        # Load models
        for model_data in data.get("models", []):
            model = ModelConfig(**model_data)
            self.models.append(model)
            
        # Load evaluation settings
        eval_data = data.get("evaluation", {})
        self.evaluation = EvaluationConfig(**eval_data)        
    def _load_prompts(self) -> None:
        """Load prompts from JSON file."""
        prompts_path = self.config_path.parent / "prompts.json"
        with open(prompts_path, 'r') as f:
            self.prompts = json.load(f)
            
    def _load_evaluation_criteria(self) -> None:
        """Load evaluation criteria from YAML file."""
        criteria_path = self.config_path.parent / "evaluation_criteria.yaml"
        with open(criteria_path, 'r') as f:
            self.evaluation_criteria = yaml.safe_load(f)
            
    def get_version_hash(self) -> str:
        """Get hash of current configuration for versioning."""
        config_str = f"{self.version}{self.global_settings}{len(self.models)}"
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
        
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.models:
            errors.append("No models configured")
            
        for model in self.models:
            if not model.name:
                errors.append("Model missing name")
            if not model.type:
                errors.append(f"Model {model.name} missing type")
            if model.type == "api" and not model.provider:
                errors.append(f"API model {model.name} missing provider")
                
        if not self.prompts:
            errors.append("No prompts loaded")
            
        return errors
