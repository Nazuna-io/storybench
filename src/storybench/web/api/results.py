"""API endpoints for results management using MongoDB."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any

from ...database.connection import get_database, init_database
from ..services.database_results_service import DatabaseResultsService
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()

# Dependency to get database results service
async def get_results_service() -> DatabaseResultsService:
    """Get database results service instance."""
    try:
        database = await get_database()
    except ConnectionError:
        # Database not initialized, initialize it
        await init_database()
        database = await get_database()
    return DatabaseResultsService(database)


@router.get("", response_model=Dict[str, Any])
async def get_results(
    config_version: Optional[str] = Query(None, description="Filter by configuration version"),
    results_service: DatabaseResultsService = Depends(get_results_service)
):
    """Get all evaluation results with optional filtering."""
    try:
        results = await results_service.get_all_results(config_version)
        versions = await results_service.get_available_versions()
        
        return {
            "results": results,
            "versions": versions,
            "total_count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")


@router.get("/versions")
async def get_result_versions(results_service: DatabaseResultsService = Depends(get_results_service)):
    """Get list of available configuration versions."""
    try:
        versions = await results_service.get_available_versions()
        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load versions: {str(e)}")


@router.get("/{model_name}", response_model=Dict[str, Any])
async def get_model_results(
    model_name: str,
    config_version: Optional[str] = Query(None, description="Specific configuration version"),
    results_service: DatabaseResultsService = Depends(get_results_service)
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
