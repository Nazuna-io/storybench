"""API endpoints for prompts management."""

from fastapi import APIRouter, HTTPException, Depends

from ..models.requests import PromptsUpdateRequest
from ..models.responses import PromptsResponse
from ..services.config_service import ConfigService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get config service
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)


@router.get("/prompts", response_model=PromptsResponse)
async def get_prompts(config_service: ConfigService = Depends(get_config_service)):
    """Get current prompts configuration."""
    try:
        prompts_data = await config_service.get_prompts()
        return PromptsResponse(prompts=prompts_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load prompts: {str(e)}")


@router.put("/prompts")
async def update_prompts(
    prompts_request: PromptsUpdateRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update prompts configuration."""
    try:
        # Convert Pydantic models to dict format expected by config
        prompts_dict = {}
        for sequence, prompts in prompts_request.prompts.items():
            prompts_dict[sequence] = [{"name": p.name, "text": p.text} for p in prompts]
        
        await config_service.update_prompts(prompts_dict)
        return {"message": "Prompts updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update prompts: {str(e)}")


@router.get("/evaluation-criteria")
async def get_evaluation_criteria(config_service: ConfigService = Depends(get_config_service)):
    """Get evaluation criteria configuration."""
    try:
        criteria = await config_service.get_evaluation_criteria()
        return criteria
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load evaluation criteria: {str(e)}")


@router.put("/evaluation-criteria")
async def update_evaluation_criteria(
    criteria: dict,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update evaluation criteria configuration."""
    try:
        await config_service.update_evaluation_criteria(criteria)
        return {"message": "Evaluation criteria updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update evaluation criteria: {str(e)}")
