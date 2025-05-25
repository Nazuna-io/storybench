"""Updated API endpoints for model configuration management using MongoDB."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..models.requests import ModelsConfigRequest, APIKeysRequest
from ..models.responses import ModelsConfigResponse, APIKeysResponse
from ...database.connection import get_database
from ...database.services.config_service import ConfigService
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()

# Dependency to get database config service
async def get_config_service() -> ConfigService:
    """Get database-backed config service instance."""
    database = await get_database()
    return ConfigService(database)


@router.get("/models", response_model=ModelsConfigResponse)
async def get_models_config(config_service: ConfigService = Depends(get_config_service)):
    """Get current model configurations from MongoDB."""
    try:
        models_config = await config_service.get_active_models()
        if not models_config:
            raise HTTPException(status_code=404, detail="No active models configuration found")
            
        # Convert to response format
        response_data = {
            "models": [model.model_dump(mode='json') for model in models_config.models],
            "evaluation": {
                "auto_evaluate": models_config.evaluation.auto_evaluate_generated_responses,
                "evaluator_models": models_config.evaluation.evaluator_llm_names,
                "max_retries": models_config.evaluation.max_retries_on_evaluation_failure
            },
            "config_hash": models_config.config_hash,
            "version": models_config.version,
            "created_at": models_config.created_at.isoformat()
        }
        return ModelsConfigResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load models config: {str(e)}")


@router.post("/models", response_model=ModelsConfigResponse)
async def update_models_config(
    request: ModelsConfigRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update model configurations in MongoDB."""
    try:
        # Save new configuration
        models_data = {
            "models": request.models,
            "evaluation": request.evaluation
        }
        
        models_config = await config_service.save_models_config(models_data)
        
        # Convert to response format
        response_data = {
            "models": [model.model_dump(mode='json') for model in models_config.models],
            "evaluation": {
                "auto_evaluate": models_config.evaluation.auto_evaluate_generated_responses,
                "evaluator_models": models_config.evaluation.evaluator_llm_names,
                "max_retries": models_config.evaluation.max_retries_on_evaluation_failure
            },
            "config_hash": models_config.config_hash,
            "version": models_config.version,
            "created_at": models_config.created_at.isoformat()
        }
        return ModelsConfigResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save models config: {str(e)}")
