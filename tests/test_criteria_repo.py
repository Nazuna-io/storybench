import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorCursor # No longer needed for manual cursor mock
from mongomock_motor import AsyncMongoMockClient

from storybench.database.models import EvaluationCriteria, EvaluationCriterionItem
from storybench.database.repositories.criteria_repo import CriteriaRepository

@pytest.fixture
def mock_db():
    # Use mongomock_motor's AsyncMongoMockClient
    client = AsyncMongoMockClient()
    return client.get_database("test_db") # Repositories usually take a db object

@pytest.fixture
def mock_collection(mock_db):
    # Get the collection from the mongomock_motor db object.
    # The name 'evaluation_criteria' is assumed from CriteriaRepository._get_collection_name
    return mock_db.evaluation_criteria

@pytest.fixture
def criteria_repo(mock_db):
    # We need to ensure that when CriteriaRepository(mock_db) is called,
    # its self.collection gets set to our mock_collection.
    # This often happens in the BaseRepository's __init__.
    # Patching _get_collection_name is a good way if it's used by BaseRepository.
    with patch.object(CriteriaRepository, '_get_collection_name', return_value='evaluation_criteria') as mock_get_name:
        repo = CriteriaRepository(mock_db)
        # Verify get_collection was called if that's the mechanism
        # If BaseRepository uses db.get_collection(self._get_collection_name()):
        # mock_db.get_collection.assert_called_with('evaluation_criteria') 
        # If BaseRepository uses db[self._get_collection_name()]:
        # mock_db.__getitem__.assert_called_with('evaluation_criteria')
    return repo

@pytest.fixture
def sample_criteria_item_data():
    return {
        "name": "Test Criterion",
        "description": "A test description",
        "scale": 5
    }

@pytest.fixture
def sample_evaluation_criteria(sample_criteria_item_data):
    criterion_item = EvaluationCriterionItem(**sample_criteria_item_data)
    # Let default_factory handle id generation
    return EvaluationCriteria(
        config_hash="testhash123",
        criteria={"crit1": criterion_item},
        version=1,
        is_active=True
    )

@pytest.mark.asyncio
async def test_create_criteria(criteria_repo, mock_collection, sample_evaluation_criteria):
    # Call the method under test
    created_doc = await criteria_repo.create(sample_evaluation_criteria)
    
    # Assertions on the returned document from create method
    assert created_doc is not None 
    assert created_doc.id == sample_evaluation_criteria.id # create() should return the model with id
    assert created_doc.config_hash == sample_evaluation_criteria.config_hash

    # Verify the document was actually inserted into mongomock
    inserted_doc_from_db = await mock_collection.find_one({"_id": sample_evaluation_criteria.id})
    assert inserted_doc_from_db is not None
    assert inserted_doc_from_db["config_hash"] == sample_evaluation_criteria.config_hash
    assert inserted_doc_from_db["version"] == sample_evaluation_criteria.version
    # Ensure PyObjectId is stored as ObjectId in mock DB if that's the behavior of model_dump(by_alias=True)
    # or check if it's string, depending on BaseRepository's implementation.
    # For mongomock, it's often fine to compare directly with ObjectId from sample_evaluation_criteria.id
    assert inserted_doc_from_db["_id"] == sample_evaluation_criteria.id

@pytest.mark.asyncio
async def test_find_active_criteria_found(criteria_repo, mock_collection, sample_evaluation_criteria):
    # Ensure the sample is active and insert it into mongomock
    sample_evaluation_criteria.is_active = True
    await mock_collection.insert_one(sample_evaluation_criteria.model_dump(by_alias=True))

    active_criteria = await criteria_repo.find_active()
    
    assert active_criteria is not None
    assert active_criteria.id == sample_evaluation_criteria.id
    assert active_criteria.is_active is True

@pytest.mark.asyncio
async def test_find_active_criteria_not_found(criteria_repo, mock_collection, sample_evaluation_criteria):
    # Ensure a non-active document is in the mock DB (or DB is empty for this specific test)
    # For this test, we want to ensure find_active returns None if no *active* criteria exist.
    # We can insert an inactive one to be sure.
    inactive_criteria = sample_evaluation_criteria.model_copy(deep=True)
    inactive_criteria.is_active = False
    inactive_criteria.config_hash = "inactive_hash_123" # Ensure different hash if needed
    await mock_collection.insert_one(inactive_criteria.model_dump(by_alias=True))
    
    # Or, ensure the collection is empty if that's the scenario to test for not found:
    # await mock_collection.delete_many({}) # Clear the collection if needed

    active_criteria = await criteria_repo.find_active()
    
    assert active_criteria is None

@pytest.mark.asyncio
async def test_find_by_config_hash_found(criteria_repo, mock_collection, sample_evaluation_criteria):
    # Ensure the sample criteria (with config_hash='testhash123') is in the mock_collection
    await mock_collection.insert_one(sample_evaluation_criteria.model_dump(by_alias=True))
    
    found_criteria = await criteria_repo.find_by_config_hash("testhash123")
    
    assert found_criteria is not None
    assert found_criteria.config_hash == "testhash123"
    assert found_criteria.id == sample_evaluation_criteria.id

@pytest.mark.asyncio
async def test_find_by_config_hash_not_found(criteria_repo, mock_collection, sample_evaluation_criteria):
    # Ensure a document with a *different* hash is in the DB, or DB is empty for this hash
    other_criteria = sample_evaluation_criteria.model_copy(deep=True)
    other_criteria.config_hash = "anotherhash789"
    await mock_collection.insert_one(other_criteria.model_dump(by_alias=True))
    
    # Or ensure the collection is empty regarding the target hash:
    # await mock_collection.delete_many({"config_hash": "nonexistenthash"})

    found_criteria = await criteria_repo.find_by_config_hash("nonexistenthash")
    
    assert found_criteria is None

@pytest.mark.asyncio
async def test_deactivate_all_criteria(criteria_repo, mock_collection, sample_evaluation_criteria):
    # Setup: Insert some active and some inactive criteria
    criteria_list = []
    active_count = 0

    # Active criteria
    for i in range(3):
        active_crit = sample_evaluation_criteria.model_copy(deep=True)
        active_crit.id = ObjectId() # New unique ID
        active_crit.config_hash = f"active_hash_{i}"
        active_crit.is_active = True
        criteria_list.append(active_crit.model_dump(by_alias=True))
        active_count += 1

    # Inactive criteria
    for i in range(2):
        inactive_crit = sample_evaluation_criteria.model_copy(deep=True)
        inactive_crit.id = ObjectId() # New unique ID
        inactive_crit.config_hash = f"inactive_hash_{i}"
        inactive_crit.is_active = False
        criteria_list.append(inactive_crit.model_dump(by_alias=True))
    
    if criteria_list:
        await mock_collection.insert_many(criteria_list)
    
    # Call the method under test
    deactivated_count = await criteria_repo.deactivate_all()
    
    # Assertions
    assert deactivated_count == active_count

    # Verify all documents in the collection are now inactive
    all_docs_after_deactivation = await mock_collection.find({}).to_list(None)
    assert len(all_docs_after_deactivation) == len(criteria_list)
    for doc in all_docs_after_deactivation:
        assert doc["is_active"] is False

    # Verify that even if no active documents existed, it runs without error
    await mock_collection.delete_many({}) # Clear collection
    # Insert only inactive criteria
    inactive_only_list = []
    for i in range(2):
        inactive_crit = sample_evaluation_criteria.model_copy(deep=True)
        inactive_crit.id = ObjectId()
        inactive_crit.config_hash = f"inactive_only_hash_{i}"
        inactive_crit.is_active = False
        inactive_only_list.append(inactive_crit.model_dump(by_alias=True))
    if inactive_only_list:
        await mock_collection.insert_many(inactive_only_list)
    
    deactivated_count_none_active = await criteria_repo.deactivate_all()
    assert deactivated_count_none_active == 0
    all_docs_after_deactivation_none_active = await mock_collection.find({}).to_list(None)
    for doc in all_docs_after_deactivation_none_active:
        assert doc["is_active"] is False
