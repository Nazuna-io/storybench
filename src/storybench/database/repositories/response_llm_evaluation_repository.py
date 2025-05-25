"""Repository for managing detailed LLM-based response evaluation documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models import ResponseLLMEvaluation, PyObjectId # PyObjectId might be needed if we query by it directly in methods
from .base import BaseRepository

class ResponseLLMEvaluationRepository(BaseRepository[ResponseLLMEvaluation]):
    """Repository for ResponseLLMEvaluation documents."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, ResponseLLMEvaluation)
        
    def _get_collection_name(self) -> str:
        return "response_llm_evaluations"
        
    async def get_evaluations_by_response_id(self, response_id: PyObjectId) -> List[ResponseLLMEvaluation]:
        """Find all LLM evaluations for a given response ID."""
        return await self.find_many({"response_id": response_id})

    async def check_if_evaluation_exists(
        self, 
        response_id: PyObjectId, 
        evaluating_llm_model: str, 
        criteria_id: PyObjectId
    ) -> bool:
        """Check if a specific evaluation (by a particular LLM model using specific criteria) already exists for a response."""
        existing = await self.find_many({
            "response_id": response_id,
            "evaluating_llm_model": evaluating_llm_model,
            "evaluation_criteria_id": criteria_id
        }, limit=1)
        return len(existing) > 0

    async def save(self, evaluation: ResponseLLMEvaluation) -> ResponseLLMEvaluation:
        """
        Create a new ResponseLLMEvaluation document.
        Returns the created document with its ID.
        """
        # The base 'create' method returns only the inserted_id.
        # For consistency or if the full document is immediately needed, we can fetch it.
        inserted_id = await super().create(evaluation)
        created_evaluation = await self.find_by_id(inserted_id)
        if not created_evaluation:
            # This should ideally not happen if create was successful
            raise Exception(f"Failed to retrieve newly created evaluation with id {inserted_id}")
        return created_evaluation

    # Placeholder for Phase 6: Manual Evaluation
    async def get_response_ids_needing_evaluation(
        self,
        # configured_evaluator_llm_names: List[str], # Names of models like "ChatGPT-Evaluator"
        # active_criteria_id: PyObjectId
        # We'll need to refine this method later. For now, it's a placeholder.
        # This might involve more complex aggregation queries against the 'responses' collection
        # and then checking against 'response_llm_evaluations'.
    ) -> List[PyObjectId]:
        """Placeholder: Finds response IDs that are missing evaluations from specified evaluators for active criteria."""
        # This is a complex query. A simpler start might be to get all response_ids
        # and then, in the service layer, check which ones are missing evaluations.
        # Or, it could find ResponseLLMEvaluation documents and group by response_id to see which ones are incomplete.
        # For now, returning an empty list.
        # Example of a more direct (but potentially slow) approach if not too many responses:
        # all_evals = await self.find_many({})
        # evaluated_response_ids = {ev.response_id for ev in all_evals}
        # This is not efficient. A proper implementation will require more thought.
        return []
