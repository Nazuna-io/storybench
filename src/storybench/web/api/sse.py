"""Server-Sent Events for real-time evaluation updates."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import asyncio
import json
from datetime import datetime

from ..services.eval_service import EvaluationService


router = APIRouter()

def get_evaluation_service():
    """Get evaluation service instance - disabled for database architecture."""
    # Note: This needs to be updated to work with database-backed services
    # For now, return None to prevent import errors
    return None


class SSEManager:
    """Manage Server-Sent Events for real-time updates."""
    
    def __init__(self):
        self._connections = set()
        self._progress_queue = asyncio.Queue()
        self._output_queue = asyncio.Queue()
        self._error_queue = asyncio.Queue()
        
    def add_connection(self, queue: asyncio.Queue):
        """Add a new SSE connection."""
        self._connections.add(queue)
        
    def remove_connection(self, queue: asyncio.Queue):
        """Remove an SSE connection."""
        self._connections.discard(queue)        
    async def send_progress_update(self, data: Dict[str, Any]):
        """Send progress update to all connected clients."""
        message = {
            "type": "progress",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self._progress_queue.put(message)
        
    async def send_output_message(self, message: str):
        """Send console output to all connected clients."""
        data = {
            "type": "output",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        await self._output_queue.put(data)
        
    async def send_error_message(self, message: str):
        """Send error message to all connected clients."""
        data = {
            "type": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        await self._error_queue.put(data)


# Global SSE manager
_sse_manager = SSEManager()


async def event_stream():
    """Generate SSE event stream."""
    client_queue = asyncio.Queue()
    _sse_manager.add_connection(client_queue)
    
    try:
        while True:
            # Check all queues for messages
            try:
                # Check progress queue
                progress_msg = _sse_manager._progress_queue.get_nowait()
                yield f"data: {json.dumps(progress_msg)}\n\n"
            except asyncio.QueueEmpty:
                pass
                
            try:
                # Check output queue  
                output_msg = _sse_manager._output_queue.get_nowait()
                yield f"data: {json.dumps(output_msg)}\n\n"
            except asyncio.QueueEmpty:
                pass
                
            try:
                # Check error queue
                error_msg = _sse_manager._error_queue.get_nowait()
                yield f"data: {json.dumps(error_msg)}\n\n"
            except asyncio.QueueEmpty:
                pass
                
            # Send heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            await asyncio.sleep(1)  # 1 second polling interval
            
    except Exception:
        pass
    finally:
        _sse_manager.remove_connection(client_queue)

@router.get("/events")
async def get_evaluation_events():
    """Get real-time evaluation events via Server-Sent Events."""
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )


def setup_sse_callbacks(eval_service=None):
    """Setup SSE callbacks for the evaluation service."""
    if eval_service is None:
        # SSE callbacks disabled for database architecture
        return
    # Original callback setup would go here
    eval_service.set_callbacks(
        progress_callback=lambda data: asyncio.create_task(_sse_manager.send_progress_update(data)),
        output_callback=lambda msg: asyncio.create_task(_sse_manager.send_output_message(msg)),
        error_callback=lambda msg: asyncio.create_task(_sse_manager.send_error_message(msg))
    )