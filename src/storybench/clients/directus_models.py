"""Pydantic models for Directus CMS data structures."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PublicationStatus(str, Enum):
    """Publication status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DirectusPrompt(BaseModel):
    """Individual prompt from Directus CMS."""
    id: int
    name: str
    text: str
    status: PublicationStatus
    sort: Optional[int] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None
    guidance_notes: Optional[str] = None
    expected_outcome_summary: Optional[str] = None
    tags: Optional[str] = None
    order_in_sequence: Optional[int] = None
    
    # Relationship to prompt sequence (not used in nested queries)
    prompt_sequence: Optional[int] = None


class DirectusPromptSequence(BaseModel):
    """Prompt sequence from Directus CMS."""
    id: int
    sequence_name: str
    sequence_description: Optional[str] = None
    status: PublicationStatus
    sort: Optional[int] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None
    
    # Many-to-many relationship through junction table
    prompts_in_sequence: Optional[List['PromptInSequence']] = None


# Junction table models for many-to-many relationships
class SequenceInSet(BaseModel):
    """Junction table entry for prompt_set_versions <-> prompt_sequences."""
    prompt_sequences_id: DirectusPromptSequence


class PromptInSequence(BaseModel):
    """Junction table entry for prompt_sequences <-> prompts."""
    prompts_id: DirectusPrompt


class DirectusPromptSetVersion(BaseModel):
    """Prompt set version from Directus CMS."""
    id: int
    version_number: int
    version_name: str
    description: Optional[str] = None
    status: PublicationStatus
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    based_on_version_number: Optional[int] = None
    
    # Many-to-many relationship through junction table
    sequences_in_set: Optional[List[SequenceInSet]] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None
    
    # Nested sequences (populated when using fields parameter)
    prompt_sequences: Optional[List[DirectusPromptSequence]] = None


class DirectusResponse(BaseModel):
    """Generic Directus API response wrapper."""
    data: Any
    meta: Optional[Dict[str, Any]] = None


class DirectusListResponse(BaseModel):
    """Directus API response for list queries."""
    data: List[Any]
    meta: Optional[Dict[str, Any]] = None


class DirectusItemResponse(BaseModel):
    """Directus API response for single item queries."""
    data: Any
    meta: Optional[Dict[str, Any]] = None


# Legacy mapping models to convert from Directus to existing MongoDB structure
class StorybenchPromptConfig(BaseModel):
    """Maps to the existing PromptItemConfig structure."""
    name: str
    text: str


class StorybenchPromptsStructure(BaseModel):
    """Maps to the existing Prompts structure used by storybench."""
    sequences: Dict[str, List[StorybenchPromptConfig]]
    version: int
    directus_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Evaluation-related models for Directus integration (following same pattern as prompts)
class DirectusEvaluationCriterion(BaseModel):
    """Individual evaluation criterion from Directus CMS."""
    id: int
    name: str          # e.g., "creativity", "coherence", "character_depth"
    description: str   # Brief description
    scale: int         # Maximum score (e.g., 5)
    criteria: str      # Full evaluation criteria with detailed instructions
    sort: Optional[int] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None


class DirectusScoring(BaseModel):
    """Scoring/evaluation prompt template from Directus CMS."""
    id: int
    name: str          # e.g., "scoring_guideline"
    guidelines: str    # Full scoring guidelines and instructions
    sort: Optional[int] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None


# Junction table models for many-to-many relationships
class CriterionInVersion(BaseModel):
    """Junction table entry for evaluation_versions <-> evaluation_criteria."""
    evaluation_criteria_id: DirectusEvaluationCriterion


class ScoringInVersion(BaseModel):
    """Junction table entry for evaluation_versions <-> scoring."""
    scoring_id: DirectusScoring


class DirectusEvaluationVersion(BaseModel):
    """Evaluation version from Directus CMS."""
    model_config = {"populate_by_name": True}  # Allow both field name and alias
    
    id: int
    version_number: int
    version_name: str
    description: Optional[str] = None
    status: PublicationStatus
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    user_created: Optional[str] = None
    user_updated: Optional[str] = None
    published_at: Optional[datetime] = Field(None, alias='pubslihed_at')  # Handle Directus typo
    published_by: Optional[str] = None
    based_on_version_number: Optional[int] = None
    
    # Many-to-many relationships through junction tables
    evaluation_criteria_in_version: Optional[List[CriterionInVersion]] = None
    scoring_in_version: Optional[List[ScoringInVersion]] = None
    
    # Nested relationships (populated when using fields parameter)
    evaluation_criteria: Optional[List[DirectusEvaluationCriterion]] = None
    scoring: Optional[List[DirectusScoring]] = None


# Legacy mapping models to convert from Directus to existing evaluation structure  
class StorybenchEvaluationCriterion(BaseModel):
    """Maps to the existing EvaluationCriteria structure."""
    name: str
    description: str
    scale: List[int]  # [min, max] e.g., [1, 5]
    criteria: str


class StorybenchEvaluationStructure(BaseModel):
    """Maps to the existing evaluation structure used by storybench."""
    criteria: Dict[str, StorybenchEvaluationCriterion]
    scoring_guidelines: str
    version: int
    version_name: str
    directus_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
