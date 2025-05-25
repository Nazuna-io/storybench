"""Updated API endpoints for prompts management using MongoDB."""

from fastapi import APIRouter, HTTPException, Depends

from ..models.requests import PromptsUpdateRequest
from ..models.responses import PromptsResponse
from ...database.connection import get_database
from ...database.services.config_service import ConfigService


router = APIRouter()

# Dependency to get database config service
async def get_config_service() -> ConfigService:
    """Get database-backed config service instance."""
    database = await get_database()
    return ConfigService(database)


@router.get("/prompts", response_model=PromptsResponse)
async def get_prompts(config_service: ConfigService = Depends(get_config_service)):
    """Get current prompts configuration from MongoDB."""
    try:
        prompts_config = await config_service.get_active_prompts()
        if not prompts_config:
            raise HTTPException(status_code=404, detail="No active prompts configuration found")
            
        response_data = {
            "prompts": {
                sequence_name: [prompt.model_dump() for prompt in prompt_list]
                for sequence_name, prompt_list in prompts_config.sequences.items()
            },
            "config_hash": prompts_config.config_hash,
            "version": prompts_config.version,
            "created_at": prompts_config.created_at.isoformat()
        }
        return PromptsResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load prompts: {str(e)}")


@router.put("/prompts")
async def update_prompts(
    request: PromptsUpdateRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update prompts configuration in MongoDB."""
    try:
        # Save new configuration
        prompts_data = {"sequences": request.prompts}
        prompts_config = await config_service.save_prompts_config(prompts_data)
        
        response_data = {
            "prompts": {
                sequence_name: [prompt.model_dump() for prompt in prompt_list]
                for sequence_name, prompt_list in prompts_config.sequences.items()
            },
            "config_hash": prompts_config.config_hash,
            "version": prompts_config.version,
            "created_at": prompts_config.created_at.isoformat()
        }
        return PromptsResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompts: {str(e)}")
