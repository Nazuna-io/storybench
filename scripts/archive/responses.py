"""Pydantic models for API responses."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

class ModelConfigResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Response model for model configuration."""
    name: str
    type: Literal["api", "local"]
    provider: Optional[str] = None
    model_name: str
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    subdirectory: Optional[str] = None


class GlobalSettingsResponse(BaseModel):
    """Response model for global settings."""
    temperature: float
    max_tokens: int
    num_runs: int
    vram_limit_percent: int


class EvaluationConfigResponse(BaseModel):
    """Response model for evaluation configuration."""
    auto_evaluate: bool
    evaluator_models: List[str]
    max_retries: int


class ModelsConfigResponse(BaseModel):
    """Response model for complete models configuration."""
    models: List[ModelConfigResponse]
    evaluation: EvaluationConfigResponse
    config_hash: str
    version: int
    created_at: str


class APIKeysResponse(BaseModel):
    """Response model for API keys (masked)."""
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    AI21_API_KEY: Optional[str] = None



class PromptResponse(BaseModel):
    """Response model for a single prompt."""
    name: str
    text: str


class PromptsResponse(BaseModel):
    """Response model for prompts."""
    prompts: Dict[str, List[PromptResponse]]
    config_hash: str
    version: int
    created_at: str


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str
    message: str
    code: str


class APIValidationResult(BaseModel):
    """API connection validation result."""
    connected: bool
    error: Optional[str] = None
    latency_ms: Optional[float] = None


class ModelValidationResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Individual model validation result."""
    model_name: str
    valid: bool
    errors: List[str] = []
    api_result: Optional[APIValidationResult] = None


class ValidationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Response model for configuration validation."""
    valid: bool
    config_errors: List[ValidationErrorDetail] = []
    api_validation: Dict[str, APIValidationResult] = {}
    model_validation: List[ModelValidationResult] = []


class ConfigVersionInfo(BaseModel):
    """Configuration version information."""
    version_hash: str
    prompts_hash: str
    criteria_hash: str
    global_settings_hash: str
    timestamp: datetime


class ProgressInfo(BaseModel):
    """Evaluation progress information."""
    total_tasks: int
    completed_tasks: int
    current_model: Optional[str] = None
    current_sequence: Optional[str] = None
    current_run: Optional[int] = None
    estimated_time_remaining: Optional[float] = None



class ResumeInfo(BaseModel):
    """Information about resumable evaluation state."""
    can_resume: bool
    models_completed: List[str] = []
    models_in_progress: List[str] = []
    models_pending: List[str] = []
    next_task: Optional[Dict[str, Any]] = None


class EvaluationStatus(BaseModel):
    """Response model for evaluation status."""
    running: bool
    current_model: Optional[str] = None
    progress: ProgressInfo
    resume_info: ResumeInfo
    config_version: str
    start_time: Optional[datetime] = None


class ResultMetadata(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Metadata for evaluation results."""
    model_name: str
    config_version: str
    config_details: Dict[str, str]
    timestamp: datetime
    last_updated: datetime


class EvaluationScores(BaseModel):
    """Evaluation scores for a model."""
    overall: Optional[float] = None
    creativity: Optional[float] = None
    coherence: Optional[float] = None
    originality: Optional[float] = None
    engagement: Optional[float] = None


class ResultSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Summary of results for results table."""
    model_name: str
    config_version: str
    status: Literal["completed", "in_progress", "failed"]
    timestamp: datetime
    scores: EvaluationScores
    total_responses: int
    successful_responses: int


class DetailedResult(BaseModel):
    """Detailed result for a specific model."""
    metadata: ResultMetadata
    sequences: Dict[str, Any]  # Detailed response data
    evaluation_scores: EvaluationScores
    status: Literal["completed", "in_progress", "failed"]


class ResultsListResponse(BaseModel):
    """Response model for results list."""
    results: List[ResultSummary]
    versions: List[str]
    total_count: int
