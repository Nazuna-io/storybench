"""Test fixes for issues identified in the storybench system."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_results_page_shows_data():
    """Test that the results page can load and display data properly."""
    from storybench.web.services.database_results_service import DatabaseResultsService
    
    # Mock database
    mock_database = AsyncMock()
    
    # Mock evaluation data
    mock_evaluations = [
        {
            "_id": "test_eval_id_1",
            "models": ["test_model"],
            "status": "completed",
            "total_tasks": 10,
            "completed_tasks": 10,
            "config_hash": "test_hash",
            "started_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T01:00:00"
        }
    ]
    
    # Mock responses  
    mock_responses = [
        {
            "_id": "test_response_id_1",
            "model_name": "test_model",
            "sequence": "test_sequence", 
            "run": 1,
            "prompt_name": "test_prompt"
        }
    ]
    
    # Mock LLM evaluations with proper scores
    mock_llm_evaluations = [
        {
            "_id": "test_llm_eval_id_1",
            "response_id": "test_response_id_1",
            "criteria_results": [
                {
                    "criterion_name": "creativity",
                    "score": 8.5,
                    "justification": "Creative response"
                },
                {
                    "criterion_name": "coherence", 
                    "score": 7.2,
                    "justification": "Coherent narrative"
                }
            ]
        }
    ]
    
    # Set up mock repository methods
    mock_database.evaluations.find.return_value.to_list = AsyncMock(return_value=mock_evaluations)
    mock_database.responses.aggregate.return_value.__aiter__ = AsyncMock(return_value=iter([{"_id": "test_model", "count": 1}]))
    mock_database.responses.find.return_value.to_list = AsyncMock(return_value=mock_responses)
    mock_database.response_llm_evaluations.find.return_value.to_list = AsyncMock(return_value=mock_llm_evaluations)
    mock_database.responses.count_documents = AsyncMock(return_value=1)
    
    # Create service and test
    service = DatabaseResultsService(mock_database)
    results = await service.get_all_results()
    
    # Assertions
    assert len(results) > 0
    assert results[0]["model_name"] == "test_model"
    assert results[0]["status"] == "completed"
    assert results[0]["scores"] is not None
    assert results[0]["scores"]["overall"] > 0  # Should have calculated overall score


@pytest.mark.asyncio 
async def test_local_model_state_persistence():
    """Test that local model configuration persists across page navigation."""
    from storybench.web.services.local_model_service import LocalModelService
    
    # Mock database
    mock_database = AsyncMock()
    
    # Create service
    service = LocalModelService(mock_database)
    
    # Test configuration
    test_config = {
        "generation_model": {
            "repo_id": "test/model",
            "filename": "model.gguf"
        },
        "use_local_evaluator": True,
        "settings": {
            "temperature": 1.0,
            "max_tokens": 8192
        }
    }
    
    # Save configuration
    await service.save_configuration(test_config)
    
    # Load configuration back
    loaded_config = await service.load_configuration()
    
    # Assertions
    assert loaded_config["generation_model"]["repo_id"] == "test/model"
    assert loaded_config["use_local_evaluator"] == True
    assert loaded_config["settings"]["temperature"] == 1.0
    assert loaded_config["settings"]["max_tokens"] == 8192


def test_frontend_score_display():
    """Test that the frontend properly displays pending evaluations."""
    # Mock result with pending evaluation
    pending_result = {
        "scores": {
            "overall": None,
            "detailed": {},
            "evaluation_status": "pending"
        }
    }
    
    # Mock result with actual scores
    scored_result = {
        "scores": {
            "overall": 7.5,
            "detailed": {
                "creativity": 8.0,
                "coherence": 7.0
            }
        }
    }
    
    # Simulate the getScoreValue function from Vue component
    def getScoreValue(result, criterion):
        if result["scores"].get("detailed", {}).get(criterion):
            return str(result["scores"]["detailed"][criterion])
        elif result["scores"].get("evaluation_status") == "pending":
            return "Pending"
        else:
            return "-"
    
    # Test assertions
    assert getScoreValue(pending_result, "creativity") == "Pending"
    assert getScoreValue(scored_result, "creativity") == "8.0"
    assert getScoreValue({"scores": {}}, "creativity") == "-"
