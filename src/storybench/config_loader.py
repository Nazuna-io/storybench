"""Configuration management for StoryBench v1.5."""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    model_id: str
    provider: str
    max_tokens: int
    enabled: bool = True
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate model configuration."""
        if not self.name or not self.model_id:
            raise ConfigurationError("Model must have name and model_id")
        if self.max_tokens <= 0:
            raise ConfigurationError(f"Invalid max_tokens for {self.name}: {self.max_tokens}")
        if self.provider not in ['anthropic', 'openai', 'google', 'deepinfra']:
            raise ConfigurationError(f"Unknown provider for {self.name}: {self.provider}")


@dataclass
class EvaluationConfig:
    """Configuration for evaluation settings."""
    evaluator_model: str
    evaluator_provider: str
    temperature_generation: float = 1.0
    temperature_evaluation: float = 0.3
    max_retries: int = 3
    retry_delay: int = 5
    retry_backoff: float = 2.0
    requests_per_minute: int = 60
    concurrent_requests: int = 1
    request_timeout: int = 300
    total_timeout: int = 3600
    
    def __post_init__(self):
        """Validate evaluation configuration."""
        if not self.evaluator_model or not self.evaluator_provider:
            raise ConfigurationError("Evaluator model and provider must be specified")
        if not 0 <= self.temperature_generation <= 2:
            raise ConfigurationError(f"Invalid temperature_generation: {self.temperature_generation}")
        if not 0 <= self.temperature_evaluation <= 2:
            raise ConfigurationError(f"Invalid temperature_evaluation: {self.temperature_evaluation}")


@dataclass
class PipelineConfig:
    """Configuration for pipeline behavior."""
    runs_per_sequence: int = 3
    sequences_to_evaluate: Union[str, List[str]] = "all"
    reset_context_between_sequences: bool = True
    preserve_context_within_sequence: bool = True
    save_checkpoints: bool = True
    checkpoint_interval: int = 5
    checkpoint_directory: str = "./checkpoints"
    continue_on_error: bool = True
    max_consecutive_errors: int = 3
    log_level: str = "INFO"
    log_file: str = "./logs/evaluation.log"
    
    def __post_init__(self):
        """Validate pipeline configuration."""
        if self.runs_per_sequence <= 0:
            raise ConfigurationError(f"Invalid runs_per_sequence: {self.runs_per_sequence}")
        if self.checkpoint_interval <= 0:
            raise ConfigurationError(f"Invalid checkpoint_interval: {self.checkpoint_interval}")
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ConfigurationError(f"Invalid log_level: {self.log_level}")


@dataclass
class StorageConfig:
    """Configuration for database storage."""
    responses_collection: str = "responses"
    evaluations_collection: str = "response_llm_evaluations"
    metadata_fields: List[str] = field(default_factory=lambda: [
        "model_name", "provider", "prompt_version", 
        "criteria_version", "pipeline_version", "timestamp"
    ])
    create_indexes: bool = True
    index_fields: List[str] = field(default_factory=lambda: [
        "model_name", "timestamp", "sequence_name"
    ])


@dataclass
class DashboardConfig:
    """Configuration for Streamlit dashboard."""
    port: int = 8501
    host: str = "0.0.0.0"
    enable_real_time: bool = True
    refresh_interval: int = 5
    max_responses_displayed: int = 1000
    enable_caching: bool = True
    cache_ttl: int = 300
    
    def __post_init__(self):
        """Validate dashboard configuration."""
        if self.port <= 0 or self.port > 65535:
            raise ConfigurationError(f"Invalid port: {self.port}")
        if self.refresh_interval <= 0:
            raise ConfigurationError(f"Invalid refresh_interval: {self.refresh_interval}")


class ConfigLoader:
    """Load and validate StoryBench configuration from YAML files."""
    
    def __init__(self, config_path: Union[str, Path] = "config/models.yaml"):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to main configuration file
        """
        self.config_path = Path(config_path)
        self._raw_config = {}
        self._models: Dict[str, List[ModelConfig]] = {}
        self._evaluation_config: Optional[EvaluationConfig] = None
        self._pipeline_config: Optional[PipelineConfig] = None
        self._storage_config: Optional[StorageConfig] = None
        self._dashboard_config: Optional[DashboardConfig] = None
        
    def load(self) -> 'ConfigLoader':
        """Load configuration from YAML file.
        
        Returns:
            Self for method chaining
            
        Raises:
            ConfigurationError: If configuration file is invalid or missing
        """
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self._raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {self.config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading {self.config_path}: {e}")
        
        # Validate and parse configuration sections
        self._parse_models()
        self._parse_evaluation()
        self._parse_pipeline()
        self._parse_storage()
        self._parse_dashboard()
        
        logger.info(f"Configuration loaded successfully from {self.config_path}")
        return self
    
    def _parse_models(self):
        """Parse and validate model configurations."""
        if 'models' not in self._raw_config:
            raise ConfigurationError("Missing 'models' section in configuration")
        
        models_config = self._raw_config['models']
        if not isinstance(models_config, dict):
            raise ConfigurationError("'models' must be a dictionary of providers")
        
        for provider, model_list in models_config.items():
            if not isinstance(model_list, list):
                raise ConfigurationError(f"Models for {provider} must be a list")
            
            self._models[provider] = []
            for model_dict in model_list:
                try:
                    model_config = ModelConfig(
                        provider=provider,
                        **model_dict
                    )
                    self._models[provider].append(model_config)
                except Exception as e:
                    raise ConfigurationError(f"Invalid model configuration: {e}")
        
        total_models = sum(len(models) for models in self._models.values())
        enabled_models = sum(
            len([m for m in models if m.enabled]) 
            for models in self._models.values()
        )
        logger.info(f"Loaded {total_models} models ({enabled_models} enabled)")
    
    def _parse_evaluation(self):
        """Parse evaluation configuration."""
        if 'evaluation' not in self._raw_config:
            raise ConfigurationError("Missing 'evaluation' section in configuration")
        
        try:
            self._evaluation_config = EvaluationConfig(**self._raw_config['evaluation'])
        except Exception as e:
            raise ConfigurationError(f"Invalid evaluation configuration: {e}")
    
    def _parse_pipeline(self):
        """Parse pipeline configuration."""
        if 'pipeline' in self._raw_config:
            try:
                self._pipeline_config = PipelineConfig(**self._raw_config['pipeline'])
            except Exception as e:
                raise ConfigurationError(f"Invalid pipeline configuration: {e}")
        else:
            self._pipeline_config = PipelineConfig()
    
    def _parse_storage(self):
        """Parse storage configuration."""
        if 'storage' in self._raw_config:
            try:
                self._storage_config = StorageConfig(**self._raw_config['storage'])
            except Exception as e:
                raise ConfigurationError(f"Invalid storage configuration: {e}")
        else:
            self._storage_config = StorageConfig()
    
    def _parse_dashboard(self):
        """Parse dashboard configuration."""
        if 'dashboard' in self._raw_config:
            try:
                self._dashboard_config = DashboardConfig(**self._raw_config['dashboard'])
            except Exception as e:
                raise ConfigurationError(f"Invalid dashboard configuration: {e}")
        else:
            self._dashboard_config = DashboardConfig()
    
    @property
    def models(self) -> Dict[str, List[ModelConfig]]:
        """Get model configurations by provider."""
        return self._models
    
    @property
    def all_models(self) -> List[ModelConfig]:
        """Get all model configurations as a flat list."""
        models = []
        for provider_models in self._models.values():
            models.extend(provider_models)
        return models
    
    @property
    def enabled_models(self) -> List[ModelConfig]:
        """Get only enabled model configurations."""
        return [m for m in self.all_models if m.enabled]
    
    @property
    def evaluation(self) -> EvaluationConfig:
        """Get evaluation configuration."""
        if not self._evaluation_config:
            raise ConfigurationError("Evaluation configuration not loaded")
        return self._evaluation_config
    
    @property
    def pipeline(self) -> PipelineConfig:
        """Get pipeline configuration."""
        if not self._pipeline_config:
            raise ConfigurationError("Pipeline configuration not loaded")
        return self._pipeline_config
    
    @property
    def storage(self) -> StorageConfig:
        """Get storage configuration."""
        if not self._storage_config:
            raise ConfigurationError("Storage configuration not loaded")
        return self._storage_config
    
    @property
    def dashboard(self) -> DashboardConfig:
        """Get dashboard configuration."""
        if not self._dashboard_config:
            raise ConfigurationError("Dashboard configuration not loaded")
        return self._dashboard_config
    
    def get_model(self, provider: str, model_name: str) -> Optional[ModelConfig]:
        """Get specific model configuration.
        
        Args:
            provider: Provider name (e.g., 'anthropic')
            model_name: Model name or model_id
            
        Returns:
            ModelConfig if found, None otherwise
        """
        if provider not in self._models:
            return None
        
        for model in self._models[provider]:
            if model.name == model_name or model.model_id == model_name:
                return model
        
        return None
    
    def validate(self) -> List[str]:
        """Validate entire configuration.
        
        Returns:
            List of validation warnings (empty if all good)
        """
        warnings = []
        
        # Check for at least one enabled model
        if not self.enabled_models:
            warnings.append("No enabled models found")
        
        # Check evaluator model exists
        evaluator_found = False
        for model in self.all_models:
            if model.model_id == self.evaluation.evaluator_model:
                evaluator_found = True
                if not model.enabled:
                    warnings.append(f"Evaluator model {model.model_id} is disabled")
                break
        
        if not evaluator_found:
            warnings.append(f"Evaluator model {self.evaluation.evaluator_model} not found in models")
        
        # Check directories exist or can be created
        dirs_to_check = [
            Path(self.pipeline.checkpoint_directory),
            Path(self.pipeline.log_file).parent
        ]
        
        for dir_path in dirs_to_check:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    warnings.append(f"Cannot create directory {dir_path}: {e}")
        
        return warnings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'models': {
                provider: [
                    {
                        'name': m.name,
                        'model_id': m.model_id,
                        'max_tokens': m.max_tokens,
                        'enabled': m.enabled,
                        'notes': m.notes
                    }
                    for m in models
                ]
                for provider, models in self._models.items()
            },
            'evaluation': self._evaluation_config.__dict__ if self._evaluation_config else {},
            'pipeline': self._pipeline_config.__dict__ if self._pipeline_config else {},
            'storage': self._storage_config.__dict__ if self._storage_config else {},
            'dashboard': self._dashboard_config.__dict__ if self._dashboard_config else {}
        }
    
    def save(self, path: Optional[Union[str, Path]] = None):
        """Save configuration to YAML file.
        
        Args:
            path: Path to save to (uses original path if not specified)
        """
        save_path = Path(path) if path else self.config_path
        
        with open(save_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {save_path}")


# Convenience functions
def load_config(config_path: Union[str, Path] = "config/models.yaml") -> ConfigLoader:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded ConfigLoader instance
    """
    return ConfigLoader(config_path).load()


def create_default_config(path: Union[str, Path] = "config/models.yaml"):
    """Create a default configuration file.
    
    Args:
        path: Where to save the default configuration
    """
    # Copy from example if it exists
    example_path = Path("config/models.example.yaml")
    target_path = Path(path)
    
    if example_path.exists():
        import shutil
        shutil.copy2(example_path, target_path)
        logger.info(f"Created default configuration from example at {target_path}")
    else:
        # Create minimal default
        default_config = {
            'models': {
                'anthropic': [{
                    'name': 'claude-3-opus',
                    'model_id': 'claude-3-opus-20240229',
                    'max_tokens': 200000,
                    'enabled': True
                }]
            },
            'evaluation': {
                'evaluator_model': 'claude-3-opus-20240229',
                'evaluator_provider': 'anthropic',
                'temperature_generation': 1.0,
                'temperature_evaluation': 0.3
            }
        }
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        logger.info(f"Created minimal default configuration at {target_path}")
