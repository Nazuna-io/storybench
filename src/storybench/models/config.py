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
    model_settings: Optional[Dict[str, Any]] = None  # For parameters like temperature, max_tokens, n_gpu_layers, etc.


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
        self._prompt_validation_errors: List[str] = []
        
    @classmethod
    def load_config(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        config = cls(config_path)
        config._load_models_config()
        config._load_prompts()
        config._load_evaluation_criteria()
        config._validate_prompts() # Perform initial validation after loading
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
        """Get hash of current configuration for versioning.
        
        Only includes factors that affect evaluation results:
        - Global settings (temperature, max_tokens, num_runs)
        - Prompts content
        - Version number
        
        Does NOT include number of models (adding models shouldn't invalidate previous results).
        """
        # Include only evaluation-affecting parameters
        config_str = (
            f"{self.version}"
            f"{self.global_settings.temperature}"
            f"{self.global_settings.max_tokens}" 
            f"{self.global_settings.num_runs}"
            f"{len(self.prompts)}"
            f"{sum(len(prompts) for prompts in self.prompts.values())}"
        )
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def _validate_prompts(self) -> None:
        """Validate the structure and content of loaded prompts."""
        self._prompt_validation_errors = []
        if not isinstance(self.prompts, dict):
            self._prompt_validation_errors.append("Prompts data must be a dictionary.")
            return

        for seq_name, prompt_list in self.prompts.items():
            if not isinstance(prompt_list, list):
                self._prompt_validation_errors.append(f"Prompt sequence '{seq_name}' must be a list.")
                continue
            # Assuming empty sequences are allowed. If not, add an error here.
            # if not prompt_list:
            #     self._prompt_validation_errors.append(f"Prompt sequence '{seq_name}' is empty.")

            for i, prompt_item in enumerate(prompt_list):
                if not isinstance(prompt_item, dict):
                    self._prompt_validation_errors.append(
                        f"Prompt item {i+1} in sequence '{seq_name}' must be a dictionary."
                    )
                    continue
                
                # Check for 'name' and 'text' keys for the prompt.
                prompt_name = prompt_item.get("name")
                prompt_content = prompt_item.get("text") # Key for actual prompt content

                if not prompt_name or not isinstance(prompt_name, str) or not prompt_name.strip():
                    self._prompt_validation_errors.append(
                        f"Prompt item {i+1} in sequence '{seq_name}' must have a non-empty 'name' (string)."
                    )
                
                if "text" not in prompt_item:
                    self._prompt_validation_errors.append(
                        f"Prompt item {i+1} (name: '{prompt_name}') in sequence '{seq_name}' is missing the 'text' field for prompt content."
                    )
                elif not isinstance(prompt_content, str) or not prompt_content.strip():
                    # Assuming prompt content should be a non-empty string for meaningful evaluation.
                    self._prompt_validation_errors.append(
                        f"Prompt item {i+1} (name: '{prompt_name}') in sequence '{seq_name}' must have a non-empty 'text' (string) for prompt content."
                    )
        
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
        # Prompt validation errors are now populated by _validate_prompts called during load
        if self._prompt_validation_errors:
            errors.extend(self._prompt_validation_errors)
            
        return errors
