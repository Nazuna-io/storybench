"""
Mock SSE (Server-Sent Events) endpoint for testing.
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import time

router = APIRouter()

@router.get("/events")
async def mock_sse_events():
    """Mock server-sent events for evaluation progress."""
    
    async def event_generator():
        while True:
            # Send a heartbeat every 5 seconds
            current_time = time.time()
            event_data = {
                "type": "heartbeat",
                "timestamp": current_time,
                "message": "Connection alive"
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )
