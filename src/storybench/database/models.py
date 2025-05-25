"""Pydantic models for MongoDB documents."""

from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from enum import Enum

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler
    ):
        from pydantic_core import core_schema
        return core_schema.no_info_before_validator_function(cls.validate, core_schema.str_schema())
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod 
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class EvaluationStatus(str, Enum):
    """Evaluation status enumeration."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class ModelType(str, Enum):
    """Model type enumeration."""
    API = "api"
    LOCAL = "local"

class ResponseStatus(str, Enum):
    """Response status enumeration."""
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

class GlobalSettings(BaseModel):
    """Global evaluation settings."""
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)
    num_runs: int = Field(default=3)
    vram_limit_percent: Optional[float] = Field(default=90.0)

class ModelConfig(BaseModel):
    """Model configuration."""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str
    type: ModelType
    provider: str
    model_name: str
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    subdirectory: Optional[str] = None

class EvaluationConfig(BaseModel):
    """Evaluation configuration."""
    auto_evaluate: bool = Field(default=True)
    evaluator_models: List[str] = Field(default_factory=list)
    max_retries: int = Field(default=3)

class PromptConfig(BaseModel):
    """Individual prompt configuration."""
    name: str
    text: str

class EvaluationCriterion(BaseModel):
    """Individual evaluation criterion."""
    name: str
    description: str
    scale: int = Field(default=10)

# MongoDB Document Models

class Evaluation(BaseModel):
    """Evaluation document model."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: EvaluationStatus = EvaluationStatus.IN_PROGRESS
    models: List[str]
    global_settings: GlobalSettings
    total_tasks: int
    completed_tasks: int = Field(default=0)
    current_model: Optional[str] = None
    current_sequence: Optional[str] = None
    current_run: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ModelConfig(BaseModel):
    """Model configuration."""
    name: str
    type: ModelType
    provider: str
    model_name: str
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    subdirectory: Optional[str] = None

class EvaluationConfig(BaseModel):
    """Evaluation configuration."""
    auto_evaluate: bool = Field(default=True)
    evaluator_models: List[str] = Field(default_factory=list)
    max_retries: int = Field(default=3)

class PromptConfig(BaseModel):
    """Individual prompt configuration."""
    name: str
    text: str

class EvaluationCriterion(BaseModel):
    """Individual evaluation criterion."""
    name: str
    description: str
    scale: int = Field(default=10)

# MongoDB Document Models

class Evaluation(BaseModel):
    """Evaluation document model."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: EvaluationStatus = EvaluationStatus.IN_PROGRESS
    models: List[str]
    global_settings: GlobalSettings
    total_tasks: int
    completed_tasks: int = Field(default=0)
    current_model: Optional[str] = None
    current_sequence: Optional[str] = None
    current_run: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ModelConfig(BaseModel):
    """Model configuration."""
    name: str
    type: ModelType
    provider: str
    model_name: str
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    subdirectory: Optional[str] = None

class EvaluationConfig(BaseModel):
    """Evaluation configuration."""
    auto_evaluate: bool = Field(default=True)
    evaluator_models: List[str] = Field(default_factory=list)
    max_retries: int = Field(default=3)

class PromptConfig(BaseModel):
    """Individual prompt configuration."""
    name: str
    text: str

class EvaluationCriterion(BaseModel):
    """Individual evaluation criterion."""
    name: str
    description: str
    scale: int = Field(default=10)

# MongoDB Document Models

class Evaluation(BaseModel):
    """Evaluation document model."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: EvaluationStatus = EvaluationStatus.IN_PROGRESS
    models: List[str]
    global_settings: GlobalSettings
    total_tasks: int
    completed_tasks: int = Field(default=0)
    current_model: Optional[str] = None
    current_sequence: Optional[str] = None
    current_run: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Models(BaseModel):
    """Models configuration document."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str
    version: int = Field(default=1)
    models: List[ModelConfig]
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Prompts(BaseModel):
    """Prompts configuration document."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str
    version: int = Field(default=1)
    sequences: Dict[str, List[PromptConfig]]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class EvaluationCriteria(BaseModel):
    """Evaluation criteria configuration document."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str
    version: int = Field(default=1)
    criteria: Dict[str, EvaluationCriterion]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Response(BaseModel):
    """Individual model response document."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    evaluation_id: PyObjectId
    model_name: str
    sequence: str
    run: int
    prompt_index: int
    prompt_name: str
    prompt_text: str
    response: str
    generation_time: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    status: ResponseStatus = ResponseStatus.COMPLETED
    error_message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class EvaluationScore(BaseModel):
    """Automated evaluation score document."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    evaluation_id: PyObjectId
    model_name: str
    sequence: str
    evaluator_model: str
    overall_score: float
    detailed_scores: Dict[str, float]
    evaluation_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
