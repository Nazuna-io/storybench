"""API endpoints for results management."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from ..models.responses import ResultsListResponse, DetailedResult, ResultSummary, EvaluationScores
from ..services.config_service import ConfigService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get config service
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)


@router.get("", response_model=ResultsListResponse)
async def get_results(
    config_version: Optional[str] = Query(None, description="Filter by configuration version"),
    config_service: ConfigService = Depends(get_config_service)
):
    """Get all evaluation results with optional filtering."""
    try:
        # Placeholder implementation for Phase 4
        return ResultsListResponse(
            results=[],
            versions=[],
            total_count=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")


@router.get("/versions")
async def get_result_versions(config_service: ConfigService = Depends(get_config_service)):
    """Get list of available configuration versions."""
    try:
        versions = await config_service.repository.get_result_versions()
        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load versions: {str(e)}")


@router.get("/{model_name}", response_model=DetailedResult)
async def get_model_results(
    model_name: str,
    config_version: Optional[str] = Query(None, description="Specific configuration version"),
    config_service: ConfigService = Depends(get_config_service)
):
    """Get detailed results for a specific model."""
    try:
        # Placeholder implementation for Phase 4
        raise HTTPException(status_code=404, detail="Results not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model results: {str(e)}")
