"""API endpoints for evaluation criteria management."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ...database.connection import get_database
from ...database.services.config_service import ConfigService
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()

# Dependency to get database config service
async def get_config_service() -> ConfigService:
    """Get database-backed config service instance."""
    database = await get_database()
    return ConfigService(database)


@router.get("/evaluation-criteria", response_model=Dict[str, Any])
async def get_criteria_config(config_service: ConfigService = Depends(get_config_service)):
    """Get current evaluation criteria from MongoDB."""
    try:
        criteria_config = await config_service.get_active_criteria()
        if not criteria_config:
            # Return default empty criteria
            return {
                "criteria": {},
                "config_hash": "default",
                "version": 1,
                "created_at": None
            }
            
        # Convert to response format
        response_data = {
            "criteria": criteria_config.criteria,
            "config_hash": criteria_config.config_hash,
            "version": criteria_config.version,
            "created_at": criteria_config.created_at.isoformat()
        }
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load criteria config: {str(e)}")


@router.put("/evaluation-criteria", response_model=Dict[str, Any])
async def update_criteria_config(
    request: Dict[str, Any],
    config_service: ConfigService = Depends(get_config_service)
):
    """Update evaluation criteria in MongoDB."""
    try:
        # Save new configuration
        criteria_config = await config_service.save_criteria_config(request)
        
        # Convert to response format
        response_data = {
            "criteria": criteria_config.criteria,
            "config_hash": criteria_config.config_hash,
            "version": criteria_config.version,
            "created_at": criteria_config.created_at.isoformat()
        }
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save criteria config: {str(e)}")
