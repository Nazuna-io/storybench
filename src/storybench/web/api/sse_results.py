"""Server-Sent Events for real-time results updates."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import asyncio
import json
from datetime import datetime, timedelta
import hashlib

from ...database.connection import get_database
from ..services.database_results_service import DatabaseResultsService

router = APIRouter()

class ResultsSSEManager:
    """Manage SSE connections for results updates."""
    
    def __init__(self):
        self._connections = set()
        self._last_results_hash = None
        self._last_check = datetime.now()
        
    def add_connection(self, queue: asyncio.Queue):
        """Add a new SSE connection."""
        self._connections.add(queue)
        
    def remove_connection(self, queue: asyncio.Queue):
        """Remove an SSE connection."""
        self._connections.discard(queue)
        
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all connected clients."""
        message = json.dumps(data)
        for connection in self._connections.copy():
            try:
                await connection.put(message)
            except Exception:
                # Remove dead connections
                self._connections.discard(connection)

# Global results SSE manager
_results_sse_manager = ResultsSSEManager()

async def get_results_service():
    """Get results service instance."""
    database = await get_database()
    return DatabaseResultsService(database)

@router.get("/results/events")
async def results_events(results_service: DatabaseResultsService = Depends(get_results_service)):
    """Stream results updates via Server-Sent Events."""
    
    async def event_generator():
        """Generate real-time results events."""
        client_queue = asyncio.Queue()
        _results_sse_manager.add_connection(client_queue)
        
        try:
            # Send initial data
            try:
                results_data = await results_service.get_all_results()
                initial_event = {
                    "type": "results_update",
                    "data": results_data,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(initial_event)}\\n\\n"
                
                # Store hash of initial data
                current_hash = hashlib.md5(json.dumps(results_data, sort_keys=True).encode()).hexdigest()
                _results_sse_manager._last_results_hash = current_hash
                
            except Exception as e:
                error_event = {
                    "type": "error",
                    "message": f"Failed to load initial results: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_event)}\\n\\n"
            
            # Monitor for changes
            while True:
                try:
                    # Check for results updates every 5 seconds
                    await asyncio.sleep(5)
                    
                    # Get current results
                    current_results = await results_service.get_all_results()
                    
                    # Create a JSON-serializable version for hashing
                    results_for_hash = json.dumps(current_results, default=str, sort_keys=True)
                    current_hash = hashlib.md5(results_for_hash.encode()).hexdigest()
                    
                    # Check if results changed
                    if current_hash != _results_sse_manager._last_results_hash:
                        update_event = {
                            "type": "results_update", 
                            "data": current_results,
                            "timestamp": datetime.now().isoformat(),
                            "change_detected": True
                        }
                        yield f"data: {json.dumps(update_event, default=str)}\\n\\n"
                        _results_sse_manager._last_results_hash = current_hash
                    
                    # Send heartbeat every 30 seconds
                    now = datetime.now()
                    if now - _results_sse_manager._last_check > timedelta(seconds=30):
                        heartbeat = {
                            "type": "heartbeat",
                            "timestamp": now.isoformat()
                        }
                        yield f"data: {json.dumps(heartbeat)}\\n\\n"
                        _results_sse_manager._last_check = now
                    
                    # Check client-specific queue for messages
                    try:
                        message = client_queue.get_nowait()
                        yield f"data: {message}\\n\\n"
                    except asyncio.QueueEmpty:
                        pass
                        
                except Exception as e:
                    error_event = {
                        "type": "error",
                        "message": f"Results monitoring error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_event)}\\n\\n"
                    await asyncio.sleep(10)  # Wait longer on error
                    
        except Exception as e:
            final_error = {
                "type": "connection_error",
                "message": f"SSE connection failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(final_error)}\\n\\n"
        finally:
            _results_sse_manager.remove_connection(client_queue)
    
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

@router.post("/results/notify")
async def notify_results_change(change_data: Dict[str, Any] = None):
    """Manually notify SSE clients of results changes (for internal use)."""
    try:
        notification = {
            "type": "manual_update",
            "data": change_data or {},
            "timestamp": datetime.now().isoformat()
        }
        await _results_sse_manager.broadcast_update(notification)
        return {"status": "success", "message": "Notification sent to all clients"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
