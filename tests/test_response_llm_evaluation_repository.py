import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime

from storybench.database.models import ResponseLLMEvaluation, CriterionEvaluation, PyObjectId
from storybench.database.repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

# Sample data for tests
RESPONSE_ID_1 = PyObjectId()
CRITERIA_ID_1 = PyObjectId()
EVAL_LLM_MODEL_1 = "gpt-4o-mini-evaluator"
FIXED_DATETIME = datetime(2024, 1, 1, 12, 0, 0)

@pytest.fixture
def mock_motor_collection():
    """Mocks an AsyncIOMotorCollection."""
    collection = AsyncMock(spec=AsyncIOMotorCollection)
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock()
    # For find_many, .find() returns a cursor, which then has methods like limit, skip, to_list
    mock_cursor = AsyncMock()
    mock_cursor.limit.return_value = mock_cursor # limit can return self for chaining
    mock_cursor.skip.return_value = mock_cursor  # skip can return self
    mock_cursor.to_list = AsyncMock()
    collection.find.return_value = mock_cursor
    return collection

@pytest.fixture
def mock_motor_database(mock_motor_collection: AsyncMock):
    """Mocks an AsyncIOMotorDatabase."""
    db = AsyncMock(spec=AsyncIOMotorDatabase)
    db.__getitem__.return_value = mock_motor_collection
    return db

@pytest.fixture
def evaluation_repo(mock_motor_database: AsyncMock):
    """Fixture for ResponseLLMEvaluationRepository with mocked database."""
    return ResponseLLMEvaluationRepository(database=mock_motor_database)

@pytest.fixture
def sample_criterion_evaluation_data():
    return {
        "criterion_name": "Clarity",
        "score": 4.0,
        "justification": "The response was clear and easy to understand."
    }

@pytest.fixture
def sample_llm_evaluation_data(sample_criterion_evaluation_data):
    """Returns a dictionary representing ResponseLLMEvaluation data."""
    return {
        "response_id": RESPONSE_ID_1,
        "evaluating_llm_provider": "openai",
        "evaluating_llm_model": EVAL_LLM_MODEL_1,
        "evaluation_criteria_id": CRITERIA_ID_1,
        "evaluation_timestamp": FIXED_DATETIME,
        "criteria_results": [sample_criterion_evaluation_data],  # List of dicts
        "raw_evaluator_output": "{\"clarity\": 4, \"justification\": \"...\"}",
        "error_message": None
    }

@pytest.fixture
def sample_llm_evaluation(sample_llm_evaluation_data):
    """Returns a ResponseLLMEvaluation Pydantic model instance."""
    # Pydantic will automatically convert the list of dicts in criteria_results
    # into List[CriterionEvaluation] objects.
    # id is typically None before the first save.
    data_for_model = sample_llm_evaluation_data.copy()
    return ResponseLLMEvaluation(id=None, **data_for_model)


class TestResponseLLMEvaluationRepository:

    def test_initialization_and_collection_name(self, evaluation_repo: ResponseLLMEvaluationRepository, mock_motor_database: AsyncMock):
        assert evaluation_repo.database == mock_motor_database
        assert evaluation_repo.model_class == ResponseLLMEvaluation
        assert evaluation_repo._get_collection_name() == "response_llm_evaluations"
        mock_motor_database.__getitem__.assert_called_once_with("response_llm_evaluations")

    @pytest.mark.asyncio
    async def test_save_evaluation(self, evaluation_repo: ResponseLLMEvaluationRepository, mock_motor_collection: AsyncMock, sample_llm_evaluation: ResponseLLMEvaluation, sample_llm_evaluation_data):
        new_eval_id = PyObjectId()
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = new_eval_id
        mock_motor_collection.insert_one.return_value = mock_insert_result
        
        # Data that find_one should return (dict form, as from DB)
        db_return_data = sample_llm_evaluation_data.copy()
        db_return_data['_id'] = new_eval_id # Add the _id that MongoDB would assign
        mock_motor_collection.find_one.return_value = db_return_data

        # sample_llm_evaluation has id=None before saving
        created_eval = await evaluation_repo.save(sample_llm_evaluation)

        # Verify insert_one call (BaseRepository.create logic)
        expected_insert_data = sample_llm_evaluation.model_dump(by_alias=True, exclude_unset=True)
        if expected_insert_data.get("_id") is None: # Pydantic might put _id: None if id was None
            expected_insert_data.pop("_id", None)
        mock_motor_collection.insert_one.assert_called_once_with(expected_insert_data)
        
        # Verify find_one call (part of repo's save method)
        mock_motor_collection.find_one.assert_called_once_with({"_id": new_eval_id})
        
        assert created_eval is not None
        assert created_eval.id == new_eval_id
        assert created_eval.response_id == sample_llm_evaluation.response_id
        assert created_eval.evaluating_llm_model == sample_llm_evaluation.evaluating_llm_model

    @pytest.mark.asyncio
    async def test_get_evaluations_by_response_id(self, evaluation_repo: ResponseLLMEvaluationRepository, mock_motor_collection: AsyncMock, sample_llm_evaluation_data):
        doc1_data_from_db = {**sample_llm_evaluation_data.copy(), "_id": PyObjectId(), "response_id": RESPONSE_ID_1}
        doc2_data_from_db = {**sample_llm_evaluation_data.copy(), "_id": PyObjectId(), "response_id": RESPONSE_ID_1, "evaluating_llm_model": "claude-evaluator"}
        
        mock_cursor = mock_motor_collection.find.return_value
        mock_cursor.to_list.return_value = [doc1_data_from_db, doc2_data_from_db]

        evaluations = await evaluation_repo.get_evaluations_by_response_id(RESPONSE_ID_1)

        mock_motor_collection.find.assert_called_once_with({"response_id": RESPONSE_ID_1})
        mock_cursor.to_list.assert_called_once_with(length=None) # BaseRepository default limit is None
        
        assert len(evaluations) == 2
        assert isinstance(evaluations[0], ResponseLLMEvaluation)
        assert evaluations[0].response_id == RESPONSE_ID_1
        assert evaluations[1].response_id == RESPONSE_ID_1
        assert evaluations[1].evaluating_llm_model == "claude-evaluator"

    @pytest.mark.asyncio
    async def test_check_if_evaluation_exists_true(self, evaluation_repo: ResponseLLMEvaluationRepository, mock_motor_collection: AsyncMock, sample_llm_evaluation_data):
        doc_from_db = {**sample_llm_evaluation_data.copy(), "_id": PyObjectId()}

        mock_cursor = mock_motor_collection.find.return_value
        mock_cursor.to_list.return_value = [doc_from_db]

        exists = await evaluation_repo.check_if_evaluation_exists(
            response_id=RESPONSE_ID_1,
            evaluating_llm_model=EVAL_LLM_MODEL_1,
            criteria_id=CRITERIA_ID_1
        )

        expected_query = {
            "response_id": RESPONSE_ID_1,
            "evaluating_llm_model": EVAL_LLM_MODEL_1,
            "evaluation_criteria_id": CRITERIA_ID_1
        }
        mock_motor_collection.find.assert_called_once_with(expected_query)
        mock_cursor.limit.assert_called_once_with(1)
        mock_cursor.to_list.assert_called_once_with(length=1)
        assert exists is True

    @pytest.mark.asyncio
    async def test_check_if_evaluation_exists_false(self, evaluation_repo: ResponseLLMEvaluationRepository, mock_motor_collection: AsyncMock):
        mock_cursor = mock_motor_collection.find.return_value
        mock_cursor.to_list.return_value = [] # No documents found

        exists = await evaluation_repo.check_if_evaluation_exists(
            response_id=RESPONSE_ID_1,
            evaluating_llm_model="non-existent-model",
            criteria_id=CRITERIA_ID_1
        )
        
        expected_query = {
            "response_id": RESPONSE_ID_1,
            "evaluating_llm_model": "non-existent-model",
            "evaluation_criteria_id": CRITERIA_ID_1
        }
        mock_motor_collection.find.assert_called_once_with(expected_query)
        mock_cursor.limit.assert_called_once_with(1)
        mock_cursor.to_list.assert_called_once_with(length=1)
        assert exists is False
