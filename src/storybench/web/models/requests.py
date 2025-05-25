"""Pydantic models for API requests."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime


class ModelConfigRequest(BaseModel):
    """Request model for updating model configuration."""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(..., description="Model name")
    type: Literal["api", "local"] = Field(..., description="Model type")
    provider: Optional[str] = Field(None, description="API provider (for API models)")
    model_name: str = Field(..., description="Model identifier")
    repo_id: Optional[str] = Field(None, description="Hugging Face repo ID (for local models)")
    filename: Optional[str] = Field(None, description="Model filename (for local models)")
    subdirectory: Optional[str] = Field(None, description="Subdirectory in repo (for local models)")


class GlobalSettingsRequest(BaseModel):
    """Request model for updating global settings."""
    temperature: float = Field(0.9, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(4096, ge=1, le=32000, description="Maximum tokens per response")
    num_runs: int = Field(3, ge=1, le=10, description="Number of runs per prompt")
    vram_limit_percent: int = Field(80, ge=10, le=100, description="VRAM usage limit percentage")


class EvaluationConfigRequest(BaseModel):
    """Request model for updating evaluation configuration."""
    auto_evaluate: bool = Field(True, description="Enable automatic evaluation")
    evaluator_models: List[str] = Field(default_factory=lambda: ["claude-3-sonnet", "gemini-pro"])
    max_retries: int = Field(5, ge=1, le=20, description="Maximum retry attempts")


class ModelsConfigRequest(BaseModel):
    """Request model for updating complete models configuration."""
    version: int = Field(1, description="Configuration version")
    global_settings: GlobalSettingsRequest
    models: List[ModelConfigRequest]
    evaluation: EvaluationConfigRequest



class APIKeysRequest(BaseModel):
    """Request model for updating API keys."""
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    AI21_API_KEY: Optional[str] = None


class PromptRequest(BaseModel):
    """Request model for a single prompt."""
    name: str = Field(..., description="Prompt name")
    text: str = Field(..., description="Prompt text")


class PromptsUpdateRequest(BaseModel):
    """Request model for updating prompts."""
    prompts: Dict[str, List[PromptRequest]] = Field(..., description="Prompts organized by sequence")


class EvaluationStartRequest(BaseModel):
    """Request model for starting an evaluation."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_names: Optional[List[str]] = Field(None, description="Models to evaluate (all if not specified)")
    resume: bool = Field(True, description="Resume from previous run if possible")


class ValidationRequest(BaseModel):
    """Request model for configuration validation."""
    test_api_connections: bool = Field(True, description="Test API connectivity")
    validate_local_models: bool = Field(False, description="Validate local model availability (disabled for API-only mode)")
    lightweight_test: bool = Field(True, description="Use lightweight API tests (faster) vs full evaluator setup")
