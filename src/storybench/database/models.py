"""Pydantic models for MongoDB documents."""

from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Callable # Callable might be used by handler
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from enum import Enum

from pydantic.json_schema import JsonSchemaValue # Added for PyObjectId
from pydantic_core import core_schema # Added for PyObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic V2.
    Handles validation from ObjectId instances or strings,
    and serializes to string for JSON.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> core_schema.CoreSchema:
        
        def validate_object_id(value: Any) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError(f"Invalid ObjectId: {value}")

        python_schema = core_schema.no_info_plain_validator_function(validate_object_id)
        
        return core_schema.json_or_python_schema(
            json_schema=core_schema.chain_schema([
                core_schema.str_schema(strip_whitespace=True),
                core_schema.no_info_plain_validator_function(validate_object_id)
            ]),
            python_schema=python_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance),
                info_arg=False,
                when_used='json'
            )
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj: core_schema.CoreSchema, handler) -> JsonSchemaValue:
        json_schema = handler(core_schema_obj)
        json_schema.update(type="string", example="507f1f77bcf86cd799439011")
        return json_schema

class EvaluationStatus(str, Enum):
    """Evaluation status enumeration."""
    IN_PROGRESS = "in_progress"
    GENERATING_RESPONSES = "generating_responses"
    RESPONSES_COMPLETE = "responses_complete"
    EVALUATING_RESPONSES = "evaluating_responses"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    STOPPED = "stopped"

class ModelType(str, Enum):
    """Model type enumeration."""
    API = "api"
    LOCAL = "local"

class ResponseStatus(str, Enum):
    """Response status enumeration."""
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

# Configuration Component Models (used within main config documents or other models)

class GlobalSettings(BaseModel):
    """Global evaluation settings."""
    temperature: float = Field(default=1.0)
    max_tokens: int = Field(default=8192)
    num_runs: int = Field(default=3)
    vram_limit_percent: Optional[float] = Field(default=90.0)

class ModelConfigItem(BaseModel): 
    """Model configuration for a single model entry."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True, arbitrary_types_allowed=True)
    
    name: str
    type: ModelType
    provider: str
    model_name: str 
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    subdirectory: Optional[str] = None

class EvaluationRunConfig(BaseModel): 
    """Configuration specific to how evaluations are run and by what."""
    auto_evaluate_generated_responses: bool = Field(default=True) 
    evaluator_llm_names: List[str] = Field(default_factory=list) 
    max_retries_on_evaluation_failure: int = Field(default=3)

class PromptItemConfig(BaseModel): 
    """Individual prompt configuration."""
    name: str
    text: str

class EvaluationCriterionItem(BaseModel): 
    """Individual evaluation criterion detail."""
    name: str
    description: str
    scale: int = 5 

class CriterionEvaluation(BaseModel):
    """Stores the evaluation for a single criterion from a single LLM evaluator."""
    criterion_name: str  
    score: Optional[float] = None 
    justification: Optional[str] = None

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
        arbitrary_types_allowed=True
    )

class ModelConfig(BaseModel):
    """Model configuration."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True, arbitrary_types_allowed=True)
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
        arbitrary_types_allowed=True
    )

class Models(BaseModel):
    """Models configuration document. Defines all available models and general evaluation settings."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str 
    version: int = Field(default=1) 
    models: List[ModelConfigItem] 
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    evaluation: EvaluationRunConfig = Field(default_factory=EvaluationRunConfig) 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True) 

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class Prompts(BaseModel):
    """Prompts configuration document. Defines all prompt sequences."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str 
    version: int = Field(default=1) 
    sequences: Dict[str, List[PromptItemConfig]] 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True) 

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class EvaluationCriteria(BaseModel):
    """Evaluation criteria configuration document. Defines the set of criteria used for LLM-based evaluation."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    config_hash: str 
    version: int = Field(default=1) 
    criteria: Dict[str, EvaluationCriterionItem] 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True) 

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class Response(BaseModel):
    """Individual model response document."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True, arbitrary_types_allowed=True)
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    evaluation_id: str  
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
        protected_namespaces=()
    )


class ResponseLLMEvaluation(BaseModel):
    """Stores the detailed, multi-criteria evaluation for a single response, performed by one external LLM."""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra='forbid'  # Ensure no unexpected fields are stored
    )

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    response_id: PyObjectId  # Links to the Response document's _id
    
    evaluating_llm_provider: str  # e.g., "openai", "google", "anthropic"
    evaluating_llm_model: str  # Specific model name from ModelConfigItem.model_name, e.g., "gpt-4o-mini"
    
    # Links to the specific version of EvaluationCriteria document used for this evaluation
    evaluation_criteria_id: PyObjectId 
    
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # List of evaluations, one for each criterion defined in the linked EvaluationCriteria
    # The order should ideally match the order in EvaluationCriteria.criteria for consistency if displayed
    criteria_results: List[CriterionEvaluation] 
    
    raw_evaluator_output: Optional[str] = None # For debugging, store the raw JSON/text from the evaluator LLM
    error_message: Optional[str] = None # If the evaluation attempt failed for this LLM

class ApiKeys(BaseModel):
    """API keys configuration document with encryption."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    provider: str  # e.g., "openai", "anthropic", etc.
    encrypted_key: str  # Encrypted API key
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
