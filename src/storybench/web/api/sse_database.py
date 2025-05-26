"""Server-Sent Events for real-time evaluation updates from database."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import asyncio
import json
from datetime import datetime

from ...database.connection import get_database
from ...database.services.evaluation_runner import DatabaseEvaluationRunner

router = APIRouter()

async def get_evaluation_runner():
    """Get database evaluation runner."""
    database = await get_database()
    return DatabaseEvaluationRunner(database)

@router.get("/events")
async def sse_events(runner: DatabaseEvaluationRunner = Depends(get_evaluation_runner)):
    """Stream evaluation events via Server-Sent Events."""
    
    async def event_generator():
        """Generate real-time evaluation events from database."""
        last_progress = None
        
        while True:
            try:
                # Check for running evaluations
                running_evaluations = await runner.find_running_evaluations()
                
                if running_evaluations:
                    # Get progress for the first running evaluation
                    evaluation = running_evaluations[0]
                    progress = await runner.get_evaluation_progress(evaluation.id)
                    
                    # Only send update if progress changed
                    if progress != last_progress:
                        event_data = {
                            "type": "progress",
                            "data": progress,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        yield f"data: {json.dumps(event_data)}\n\n"
                        last_progress = progress
                        
                        # Send console output for current activity
                        if progress and progress.get("current_model"):
                            message = f"Processing {progress['current_model']}"
                            if progress.get("current_sequence"):
                                message += f" - {progress['current_sequence']}"
                            if progress.get("current_run"):
                                message += f" (Run {progress['current_run']})"
                                
                            output_event = {
                                "type": "output",
                                "message": message,
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(output_event)}\n\n"
                else:
                    # No running evaluations, send heartbeat
                    heartbeat = {
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
                
                # Wait 2 seconds before next check
                await asyncio.sleep(2)
                
            except Exception as e:
                error_event = {
                    "type": "error",
                    "message": f"SSE error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                await asyncio.sleep(5)  # Wait longer on error
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
