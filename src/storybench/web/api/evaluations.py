"""Updated API endpoints for evaluation management using MongoDB."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from bson import ObjectId

from ..models.requests import EvaluationStartRequest
from ..models.responses import EvaluationStatus, ProgressInfo, ResumeInfo
from ...database.connection import get_database, init_database
from ...database.services.evaluation_runner import DatabaseEvaluationRunner
from ...database.services.config_service import ConfigService
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()

# Dependency to get database evaluation runner
async def get_evaluation_runner() -> DatabaseEvaluationRunner:
    """Get database-backed evaluation runner."""
    try:
        # Try to get existing database connection first
        try:
            database = await get_database()
        except ConnectionError:
            # If no connection exists, initialize it
            database = await init_database()
        
        return DatabaseEvaluationRunner(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize evaluation runner: {str(e)}")

async def get_config_service() -> ConfigService:
    """Get database-backed config service."""
    try:
        # Try to get existing database connection first
        try:
            database = await get_database()
        except ConnectionError:
            # If no connection exists, initialize it
            database = await init_database()
            
        return ConfigService(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize config service: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_evaluation_status(
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Get current evaluation status."""
    try:
        # Find any running evaluations
        running_evaluations = await runner.find_running_evaluations()
        
        if not running_evaluations:
            return {
                "running": False,
                "status": "idle",
                "progress": None
            }
        
        # Get the most recent running evaluation
        current_eval = running_evaluations[0]
        progress = await runner.get_evaluation_progress(current_eval.id)
        
        return {
            "running": True,
            "status": "running",
            "evaluation_id": str(current_eval.id),
            "progress": progress
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation status: {str(e)}")


@router.get("/resume-status", response_model=Dict[str, Any])
async def get_resume_status(
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Get resume status for incomplete evaluations."""
    try:
        # Find incomplete evaluations
        incomplete_evaluations = await runner.find_incomplete_evaluations()
        
        if not incomplete_evaluations:
            return {
                "resume_info": {
                    "can_resume": False,
                    "models_completed": [],
                    "models_in_progress": [],
                    "models_pending": []
                }
            }
        
        # Get the most recent incomplete evaluation
        latest_incomplete = incomplete_evaluations[0]
        progress = await runner.get_evaluation_progress(latest_incomplete.id)
        
        # Extract model status information
        models_completed = []
        models_in_progress = []
        models_pending = []
        
        if progress and "models" in progress:
            for model_name, model_info in progress["models"].items():
                if model_info.get("status") == "completed":
                    models_completed.append(model_name)
                elif model_info.get("status") in ["running", "in_progress"]:
                    models_in_progress.append(model_name)
                else:
                    models_pending.append(model_name)
        
        return {
            "resume_info": {
                "can_resume": True,
                "evaluation_id": str(latest_incomplete.id),
                "models_completed": models_completed,
                "models_in_progress": models_in_progress,
                "models_pending": models_pending
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resume status: {str(e)}")


@router.post("/stop", response_model=Dict[str, Any])
async def stop_evaluation(
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Stop any currently running evaluation."""
    try:
        # Find running evaluations
        running_evaluations = await runner.find_running_evaluations()
        
        if not running_evaluations:
            return {
                "status": "no_running_evaluation",
                "message": "No evaluation currently running"
            }
        
        # Stop all running evaluations
        stopped_count = 0
        for evaluation in running_evaluations:
            success = await runner.stop_evaluation(evaluation.id)
            if success:
                stopped_count += 1
        
        return {
            "status": "stopped",
            "message": f"Stopped {stopped_count} running evaluation(s)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop evaluation: {str(e)}")


@router.post("/start", response_model=Dict[str, Any])
async def start_evaluation(
    request: EvaluationStartRequest,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner),
    config_service: ConfigService = Depends(get_config_service)
):
    """Start a new evaluation using database storage."""
    try:
        # Check if there's already a running evaluation
        running_evaluations = await runner.find_running_evaluations()
        if running_evaluations:
            raise HTTPException(
                status_code=400, 
                detail="An evaluation is already running. Please stop it before starting a new one."
            )
        
        # Get active configurations from database
        models_config = await config_service.get_active_models()
        prompts_config = await config_service.get_active_prompts()
        criteria_config = await config_service.get_active_criteria()
        
        if not models_config or not prompts_config or not criteria_config:
            raise HTTPException(status_code=400, detail="Missing required configurations")
            
        # Extract data for evaluation
        models = [model.name for model in models_config.models]
        sequences = {name: [prompt.model_dump() for prompt in prompt_list] 
                    for name, prompt_list in prompts_config.sequences.items()}
        criteria = {name: criterion.model_dump() for name, criterion in criteria_config.criteria.items()}
        global_settings = models_config.evaluation.model_dump()
        
        # Start evaluation
        evaluation = await runner.start_evaluation(
            models=models,
            sequences=sequences,
            criteria=criteria,
            global_settings=global_settings
        )
        
        return {
            "evaluation_id": str(evaluation.id),
            "status": "started",
            "total_tasks": evaluation.total_tasks,
            "config_hash": evaluation.config_hash
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start evaluation: {str(e)}")

@router.get("/{evaluation_id}/progress", response_model=Dict[str, Any])
async def get_evaluation_progress(
    evaluation_id: str,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Get real-time progress for an evaluation."""
    try:
        # Convert string ID to ObjectId
        eval_id = ObjectId(evaluation_id)
        
        # Get progress from database
        progress = await runner.get_evaluation_progress(eval_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Evaluation not found")
            
        return progress
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.get("/incomplete", response_model=List[Dict[str, Any]])
async def get_incomplete_evaluations(
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Get list of evaluations that can be resumed."""
    try:
        incomplete_evaluations = await runner.find_incomplete_evaluations()
        
        result = []
        for evaluation in incomplete_evaluations:
            progress = await runner.get_evaluation_progress(evaluation.id)
            if progress:
                result.append(progress)
                
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get incomplete evaluations: {str(e)}")


@router.post("/{evaluation_id}/complete")
async def mark_evaluation_complete(
    evaluation_id: str,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Mark an evaluation as completed."""
    try:
        eval_id = ObjectId(evaluation_id)
        await runner.mark_evaluation_completed(eval_id)
        
        return {"status": "completed"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark evaluation complete: {str(e)}")


@router.post("/{evaluation_id}/fail")
async def mark_evaluation_failed(
    evaluation_id: str,
    error_message: str,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Mark an evaluation as failed."""
    try:
        eval_id = ObjectId(evaluation_id)
        await runner.mark_evaluation_failed(eval_id, error_message)
        
        return {"status": "failed", "error": error_message}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark evaluation failed: {str(e)}")

@router.get("/{evaluation_id}/stream")
async def stream_evaluation_progress(
    evaluation_id: str,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Stream real-time progress updates for an evaluation."""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def progress_generator():
        """Generate progress updates from database."""
        try:
            eval_id = ObjectId(evaluation_id)
            
            while True:
                progress = await runner.get_evaluation_progress(eval_id)
                
                if not progress:
                    yield f"data: {json.dumps({'error': 'Evaluation not found'})}\n\n"
                    break
                    
                yield f"data: {json.dumps(progress)}\n\n"
                
                # Break if evaluation is complete
                if progress["status"] in ["completed", "failed"]:
                    break
                    
                # Wait 2 seconds before next update
                await asyncio.sleep(2)
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        progress_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/{evaluation_id}/pause")
async def pause_evaluation(
    evaluation_id: str,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Pause an evaluation."""
    try:
        eval_id = ObjectId(evaluation_id)
        success = await runner.pause_evaluation(eval_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Evaluation not found")
            
        return {"status": "paused"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause evaluation: {str(e)}")


@router.post("/{evaluation_id}/resume")
async def resume_evaluation(
    evaluation_id: str,
    runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)
):
    """Resume a paused evaluation."""
    try:
        eval_id = ObjectId(evaluation_id)
        success = await runner.resume_evaluation(eval_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Evaluation not found")
            
        return {"status": "resumed"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume evaluation: {str(e)}")
