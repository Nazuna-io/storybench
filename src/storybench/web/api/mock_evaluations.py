"""
Mock evaluations API for testing without database dependency.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio

from ..services.mock_evaluation_service import mock_state

router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
async def get_evaluation_status():
    """Get current evaluation status (mock)."""
    await asyncio.sleep(0.1)  # Simulate async delay
    return mock_state.get_status()

@router.get("/resume-status", response_model=Dict[str, Any])
async def get_resume_status():
    """Get resume status (mock)."""
    await asyncio.sleep(0.1)  # Simulate async delay
    return mock_state.get_resume_info()

@router.post("/start", response_model=Dict[str, Any])
async def start_evaluation(request: dict = None):
    """Start evaluation (mock)."""
    resume = request.get("resume", False) if request else False
    mock_state.start_evaluation(resume)
    
    return {
        "evaluation_id": mock_state.evaluation_id,
        "status": "started",
        "total_tasks": mock_state.progress["total_tasks"],
        "config_hash": "mock_config_123"
    }

@router.post("/stop", response_model=Dict[str, Any])
async def stop_evaluation():
    """Stop evaluation (mock)."""
    if not mock_state.is_running:
        return {
            "status": "no_running_evaluation",
            "message": "No evaluation currently running"
        }
    
    mock_state.stop_evaluation()
    return {
        "status": "stopped",
        "message": "Stopped evaluation"
    }
