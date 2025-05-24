"""API endpoints for model configuration management."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..models.requests import ModelsConfigRequest, APIKeysRequest
from ..models.responses import ModelsConfigResponse, APIKeysResponse
from ..services.config_service import ConfigService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get config service
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)


@router.get("/models", response_model=ModelsConfigResponse)
async def get_models_config(config_service: ConfigService = Depends(get_config_service)):
    """Get current model configurations."""
    try:
        config_data = await config_service.get_models_config()
        return ModelsConfigResponse(**config_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load models config: {str(e)}")


@router.put("/models")
async def update_models_config(
    config: ModelsConfigRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update model configurations."""
    try:
        # Convert Pydantic model to dict for saving
        config_dict = config.dict()
        await config_service.update_models_config(config_dict)
        return {"message": "Models configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update models config: {str(e)}")


@router.get("/api-keys", response_model=APIKeysResponse)
async def get_api_keys(config_service: ConfigService = Depends(get_config_service)):
    """Get current API keys (masked)."""
    try:
        keys = await config_service.get_api_keys()
        return APIKeysResponse(**keys)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load API keys: {str(e)}")


@router.put("/api-keys")
async def update_api_keys(
    keys: APIKeysRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update API keys."""
    try:
        # Only update keys that are provided (not None)
        keys_dict = {k: v for k, v in keys.dict().items() if v is not None}
        await config_service.update_api_keys(keys_dict)
        return {"message": "API keys updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update API keys: {str(e)}")
