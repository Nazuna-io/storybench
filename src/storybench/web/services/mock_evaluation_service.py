"""
Mock evaluation system for testing frontend functionality.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

class MockEvaluationState:
    """Simple in-memory evaluation state for testing."""
    
    def __init__(self):
        self.is_running = False
        self.evaluation_id = None
        self.progress = {
            "total_tasks": 100,
            "completed_tasks": 0,
            "current_model": None,
            "current_sequence": None,
            "current_run": None
        }
        self.can_resume = True  # Simulate having a resumable evaluation
        self.resume_info = {
            "can_resume": True,
            "models_completed": ["GPT-4o"],
            "models_in_progress": [],
            "models_pending": ["Claude-4-Sonnet", "Gemini-2.5-Pro"]
        }
        
    def start_evaluation(self, resume=False):
        """Start or resume an evaluation."""
        self.is_running = True
        self.evaluation_id = "mock_eval_123"
        if resume:
            self.progress["completed_tasks"] = 45
            self.progress["current_model"] = "Claude-4-Sonnet"
            self.progress["current_sequence"] = "FilmNarrative"
            self.progress["current_run"] = 2
        else:
            self.progress["completed_tasks"] = 0
            self.progress["current_model"] = "GPT-4o"
            self.progress["current_sequence"] = "FilmNarrative" 
            self.progress["current_run"] = 1
            
    def stop_evaluation(self):
        """Stop the evaluation."""
        self.is_running = False
        self.evaluation_id = None
        
    def get_status(self):
        """Get current status."""
        return {
            "running": self.is_running,
            "status": "running" if self.is_running else "idle",
            "evaluation_id": self.evaluation_id,
            "progress": self.progress if self.is_running else None
        }
        
    def get_resume_info(self):
        """Get resume information."""
        return {"resume_info": self.resume_info}

# Global mock state
mock_state = MockEvaluationState()
