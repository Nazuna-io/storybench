"""API endpoints for evaluation management."""

from fastapi import APIRouter, HTTPException, Depends

from ..models.requests import EvaluationStartRequest
from ..models.responses import EvaluationStatus, ProgressInfo, ResumeInfo
from ..services.config_service import ConfigService
from ..repositories.file_repository import FileRepository


router = APIRouter()

# Dependency to get config service
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)


@router.post("/start")
async def start_evaluation(
    request: EvaluationStartRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Start evaluation process."""
    # Placeholder for Phase 5 implementation
    return {"message": "Evaluation start not yet implemented"}


@router.get("/status", response_model=EvaluationStatus)
async def get_evaluation_status(config_service: ConfigService = Depends(get_config_service)):
    """Get current evaluation status."""
    # Placeholder implementation
    config_version = await config_service.get_configuration_version_hash()
    
    return EvaluationStatus(
        running=False,
        current_model=None,
        progress=ProgressInfo(
            total_tasks=0,
            completed_tasks=0
        ),
        resume_info=ResumeInfo(
            can_resume=False,
            models_completed=[],
            models_in_progress=[],
            models_pending=[]
        ),
        config_version=config_version
    )


@router.post("/stop")
async def stop_evaluation():
    """Stop running evaluation."""
    # Placeholder for Phase 5 implementation
    return {"message": "Evaluation stop not yet implemented"}


@router.get("/resume-status")
async def get_resume_status():
    """Check if evaluation can be resumed."""
    # Placeholder for Phase 5 implementation
    return {"can_resume": False, "message": "Resume status not yet implemented"}
