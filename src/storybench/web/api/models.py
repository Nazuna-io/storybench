"""Updated API endpoints for model configuration management using MongoDB."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..models.requests import ModelsConfigRequest, APIKeysRequest
from ..models.responses import ModelsConfigResponse, APIKeysResponse
from ...database.connection import get_database
from ...database.services.config_service import ConfigService
from ...database.repositories.api_keys_repo import ApiKeysRepository
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()

# Dependency to get database config service
async def get_config_service() -> ConfigService:
    """Get database-backed config service instance."""
    database = await get_database()
    return ConfigService(database)

async def get_api_keys_repo() -> ApiKeysRepository:
    """Get API keys repository instance."""
    database = await get_database()
    return ApiKeysRepository(database)


@router.get("/models", response_model=Dict[str, Any])
async def get_models_config(config_service: ConfigService = Depends(get_config_service)):
    """Get current model configurations from MongoDB."""
    try:
        models_config = await config_service.get_active_models()
        if not models_config:
            # Return default configuration
            return {
                "models": [],
                "global_settings": {
                    "temperature": 1.0,
                    "max_tokens": 8192,
                    "num_runs": 3,
                    "vram_limit_percent": 90
                },
                "evaluation": {
                    "auto_evaluate": True,
                    "evaluator_models": [],
                    "max_retries": 3
                }
            }
            
        # Convert to response format
        response_data = {
            "models": [model.model_dump(mode='json') for model in models_config.models],
            "global_settings": models_config.global_settings.model_dump(),
            "evaluation": {
                "auto_evaluate": models_config.evaluation.auto_evaluate_generated_responses,
                "evaluator_models": models_config.evaluation.evaluator_llm_names,
                "max_retries": models_config.evaluation.max_retries_on_evaluation_failure
            },
            "config_hash": models_config.config_hash,
            "version": models_config.version,
            "created_at": models_config.created_at.isoformat()
        }
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load models config: {str(e)}")


@router.put("/models", response_model=Dict[str, Any])
async def update_models_config(
    request: Dict[str, Any],
    config_service: ConfigService = Depends(get_config_service)
):
    """Update model configurations in MongoDB."""
    try:
        # Save new configuration
        models_config = await config_service.save_models_config(request)
        
        # Convert to response format
        response_data = {
            "models": [model.model_dump(mode='json') for model in models_config.models],
            "global_settings": models_config.global_settings.model_dump(),
            "evaluation": {
                "auto_evaluate": models_config.evaluation.auto_evaluate_generated_responses,
                "evaluator_models": models_config.evaluation.evaluator_llm_names,
                "max_retries": models_config.evaluation.max_retries_on_evaluation_failure
            },
            "config_hash": models_config.config_hash,
            "version": models_config.version,
            "created_at": models_config.created_at.isoformat()
        }
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save models config: {str(e)}")


@router.get("/api-keys", response_model=Dict[str, str])
async def get_api_keys(api_keys_repo: ApiKeysRepository = Depends(get_api_keys_repo)):
    """Get masked API keys for display."""
    try:
        masked_keys = await api_keys_repo.get_all_masked_keys()
        return masked_keys
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load API keys: {str(e)}")


@router.put("/api-keys", response_model=Dict[str, str])
async def update_api_keys(
    keys: Dict[str, str],
    api_keys_repo: ApiKeysRepository = Depends(get_api_keys_repo)
):
    """Update API keys in the database."""
    try:
        saved_keys = {}
        for provider, key in keys.items():
            if key:  # Only save non-empty keys
                success = await api_keys_repo.save_api_key(provider, key)
                if success:
                    saved_keys[provider] = "saved"
                else:
                    saved_keys[provider] = "failed"
        
        return {"status": "success", "saved": saved_keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save API keys: {str(e)}")


@router.post("/test-api-key", response_model=Dict[str, Any])
async def test_api_key(request: Dict[str, str]):
    """Test an API key for validity."""
    try:
        provider = request.get("provider")
        api_key = request.get("api_key")
        
        if not provider or not api_key:
            raise HTTPException(status_code=400, detail="Provider and API key are required")
        
        # Simple validation - in a real implementation, you'd make a minimal API call
        # For now, just check the key format
        if provider == "openai" and not api_key.startswith("sk-"):
            return {"success": False, "error": "OpenAI API keys should start with 'sk-'"}
        elif provider == "anthropic" and not api_key.startswith("sk-ant-"):
            return {"success": False, "error": "Anthropic API keys should start with 'sk-ant-'"}
        elif provider == "google" and len(api_key) < 20:
            return {"success": False, "error": "Google API key appears too short"}
        
        # If format looks good, return success
        return {"success": True, "message": f"{provider.title()} API key format is valid"}
        
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}
