"""API endpoints for local model operations."""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from ..models.requests import ModelConfigRequest
from ..services.local_model_service import LocalModelService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/local-models", tags=["local-models"])

# Global variables for SSE
output_queue = asyncio.Queue()
progress_queue = asyncio.Queue()
evaluation_status = {"status": "idle", "progress": 0, "download_progress": 0}


async def get_database():
    """Get database connection."""
    try:
        from ...database.connection import get_database
        return await get_database()
    except Exception as e:
        logger.warning(f"Could not connect to database: {str(e)}")
        return None


async def get_local_model_service(database = Depends(get_database)):
    """Get local model service instance."""
    service = LocalModelService(database)
    
    # Register output callback
    def output_callback(message, message_type="info"):
        asyncio.create_task(
            output_queue.put({
                "type": "console",
                "console_type": message_type,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        )
    
    # Register progress callback
    def progress_callback(progress_percent, status_message):
        global evaluation_status
        evaluation_status["download_progress"] = progress_percent
        
        asyncio.create_task(
            output_queue.put({
                "type": "progress",
                "progress": progress_percent,
                "message": status_message,
                "timestamp": datetime.now().isoformat()
            })
        )
    
    service.register_output_callback(output_callback)
    service.register_progress_callback(progress_callback)
    return service


@router.get("/config")
async def get_local_model_config(
    service: LocalModelService = Depends(get_local_model_service)
):
    """Get local model configuration."""
    try:
        config = await service.load_configuration()
        return config
    except Exception as e:
        logger.error(f"Error loading local model configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def save_local_model_config(
    config: Dict[str, Any],
    service: LocalModelService = Depends(get_local_model_service)
):
    """Save local model configuration."""
    try:
        await service.save_configuration(config)
        return {"success": True, "message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Error saving local model configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hardware-info")
async def get_hardware_info(
    service: LocalModelService = Depends(get_local_model_service)
):
    """Get hardware information."""
    try:
        info = await service.get_hardware_info()
        return info
    except Exception as e:
        logger.error(f"Error getting hardware information: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_local_evaluation(
    config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    service: LocalModelService = Depends(get_local_model_service)
):
    """Start local model evaluation."""
    global evaluation_status
    
    if evaluation_status["status"] != "idle":
        raise HTTPException(status_code=400, detail="Evaluation already running")
    
    # Update status
    evaluation_status = {"status": "in_progress", "progress": 0}
    
    # Send status update to SSE
    await output_queue.put({
        "type": "status",
        "status": "in_progress",
        "progress": 0,
        "timestamp": datetime.now().isoformat()
    })
    
    # Get API keys from environment
    api_keys = {
        "openai": os.environ.get("OPENAI_API_KEY", ""),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
        "google": os.environ.get("GOOGLE_API_KEY", "")
    }
    
    # Run evaluation in background
    async def run_evaluation():
        global evaluation_status
        try:
            await service.run_local_evaluation(
                generation_model=config.get("generation_model", {}),
                evaluation_model=config.get("evaluation_model"),
                use_local_evaluator=config.get("use_local_evaluator", False),
                sequences=config.get("sequences", []),
                settings=config.get("settings", {}),
                api_keys=api_keys
            )
            # Update status
            evaluation_status = {"status": "completed", "progress": 100}
            # Send status update to SSE
            await output_queue.put({
                "type": "status",
                "status": "completed",
                "progress": 100,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error running local evaluation: {str(e)}")
            # Update status
            evaluation_status = {"status": "failed", "progress": 0, "error": str(e)}
            # Send status update to SSE
            await output_queue.put({
                "type": "status",
                "status": "failed",
                "progress": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            # Send error message to console
            await output_queue.put({
                "type": "console",
                "console_type": "error",
                "message": f"Evaluation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    background_tasks.add_task(run_evaluation)
    
    return {"success": True, "message": "Evaluation started"}


@router.get("/status")
async def get_evaluation_status():
    """Get current evaluation status."""
    return evaluation_status


@router.post("/stop")
async def stop_evaluation():
    """Stop running evaluation."""
    global evaluation_status
    
    if evaluation_status["status"] not in ["in_progress", "generating_responses", "evaluating_responses"]:
        raise HTTPException(status_code=400, detail="No evaluation running")
    
    # Update status
    evaluation_status = {"status": "stopped", "progress": 0}
    
    # Send status update to SSE
    await output_queue.put({
        "type": "status",
        "status": "stopped",
        "progress": 0,
        "timestamp": datetime.now().isoformat()
    })
    
    # TODO: Implement actual stopping of evaluation
    
    return {"success": True, "message": "Evaluation stopped"}


@router.get("/events")
async def event_stream(request: Request):
    """SSE endpoint for real-time updates."""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
                
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(output_queue.get(), timeout=1.0)
                
                # Format message for SSE
                if isinstance(message, dict):
                    # Extract the message type and use it as the event name
                    msg_type = message.pop("type", "message")
                    # Convert the remaining data to JSON
                    data = json.dumps(message)
                    # Yield a properly formatted SSE message
                    yield {"event": msg_type, "data": data}
                else:
                    # If it's not a dict, just send it as data
                    yield {"data": json.dumps(message)}
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                yield {"event": "ping", "data": json.dumps({"timestamp": datetime.now().isoformat()})}
            except Exception as e:
                logger.error(f"Error in SSE: {str(e)}")
                yield {"event": "error", "data": json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()})}
                break
    
    return EventSourceResponse(event_generator())
