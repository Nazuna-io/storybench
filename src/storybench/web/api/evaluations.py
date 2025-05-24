"""API endpoints for evaluation management."""

from fastapi import APIRouter, HTTPException, Depends
import os
from typing import Dict, Any

from ..models.requests import EvaluationStartRequest
from ..models.responses import EvaluationStatus, ProgressInfo, ResumeInfo
from ..services.config_service import ConfigService
from ..services.eval_service import EvaluationService
from ..repositories.file_repository import FileRepository
from ...models.config import Config


router = APIRouter()

# Global evaluation service instance
_eval_service = EvaluationService()

# Dependency to get config service
def get_config_service() -> ConfigService:
    """Get config service instance."""
    repository = FileRepository()
    return ConfigService(repository)

def get_evaluation_service() -> EvaluationService:
    """Get evaluation service instance."""
    return _eval_service

def _get_api_keys() -> Dict[str, str]:
    """Get API keys from environment variables."""
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"), 
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "QWEN_API_KEY": os.getenv("QWEN_API_KEY"),
        "AI21_API_KEY": os.getenv("AI21_API_KEY")
    }
def _check_required_api_keys(models, api_keys) -> list:
    """Check if required API keys are present."""
    provider_key_map = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'qwen': 'QWEN_API_KEY',
        'ai21': 'AI21_API_KEY'
    }
    
    required_keys = set()
    for model in models:
        if model.type == 'api' and model.provider:
            key_name = provider_key_map.get(model.provider.lower())
            if key_name:
                required_keys.add(key_name)
    
    missing = []
    for key in required_keys:
        if not api_keys.get(key):
            missing.append(key)
    
    return missing


@router.post("/start")
async def start_evaluation(
    request: EvaluationStartRequest,
    config_service: ConfigService = Depends(get_config_service),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Start evaluation process."""
    try:
        # Load current configuration
        config = await config_service.load_config()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise HTTPException(status_code=400, detail=f"Configuration errors: {', '.join(errors)}")
        
        # Check API keys
        api_keys = _get_api_keys()
        missing_keys = _check_required_api_keys(config.models, api_keys)
        if missing_keys:
            raise HTTPException(status_code=400, detail=f"Missing API keys: {', '.join(missing_keys)}")
        
        # Start evaluation
        success = await eval_service.start_evaluation(config, api_keys, request.resume)
        
        if success:
            return {"message": "Evaluation started successfully", "status": "started"}
        else:
            raise HTTPException(status_code=409, detail="Evaluation already running")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=EvaluationStatus)
async def get_evaluation_status(
    config_service: ConfigService = Depends(get_config_service),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Get current evaluation status."""
    try:
        config = await config_service.load_config()
        config_version = config.get_version_hash()
        
        # Get current status from evaluation service
        status = eval_service.get_status()
        
        # Get resume information
        resume_info = await eval_service.get_resume_status(config)
        
        return EvaluationStatus(
            running=status["running"],
            current_model=status["current_model"],
            progress=ProgressInfo(
                total_tasks=status["total_tasks"],
                completed_tasks=status["completed_tasks"],
                current_model=status["current_model"],
                current_sequence=status["current_sequence"],
                current_run=status["current_run"]
            ),
            resume_info=resume_info,
            config_version=config_version
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_evaluation(eval_service: EvaluationService = Depends(get_evaluation_service)):
    """Stop running evaluation."""
    try:
        success = await eval_service.stop_evaluation()
        
        if success:
            return {"message": "Evaluation stopped successfully", "status": "stopped"}
        else:
            return {"message": "No evaluation running", "status": "not_running"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resume-status")
async def get_resume_status(
    config_service: ConfigService = Depends(get_config_service),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    """Check if evaluation can be resumed."""
    try:
        config = await config_service.load_config()
        resume_info = await eval_service.get_resume_status(config)
        
        return {
            "can_resume": resume_info.can_resume,
            "resume_info": resume_info.dict(),
            "message": "Resume status retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))