"""API endpoints for results management."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from ..models.responses import ResultsListResponse, DetailedResult, ResultSummary, EvaluationScores
from ..services.config_service import ConfigService
from ..services.results_service import ResultsService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get services
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)

def get_results_service() -> ResultsService:
    """Get results service instance."""
    return ResultsService()


@router.get("", response_model=ResultsListResponse)
async def get_results(
    config_version: Optional[str] = Query(None, description="Filter by configuration version"),
    results_service: ResultsService = Depends(get_results_service)
):
    """Get all evaluation results with optional filtering."""
    try:
        results = await results_service.get_all_results(config_version)
        versions = await results_service.get_available_versions()
        
        return ResultsListResponse(
            results=results,
            versions=versions,
            total_count=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")


@router.get("/versions")
async def get_result_versions(results_service: ResultsService = Depends(get_results_service)):
    """Get list of available configuration versions."""
    try:
        versions = await results_service.get_available_versions()
        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load versions: {str(e)}")


@router.get("/{model_name}", response_model=DetailedResult)
async def get_model_results(
    model_name: str,
    config_version: Optional[str] = Query(None, description="Specific configuration version"),
    results_service: ResultsService = Depends(get_results_service)
):
    """Get detailed results for a specific model."""
    try:
        result = await results_service.get_detailed_result(model_name, config_version)
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model results: {str(e)}")
