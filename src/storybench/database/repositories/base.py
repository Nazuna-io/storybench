"""Base repository class with common CRUD operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pydantic import BaseModel
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T], ABC):
    """Base repository class providing common database operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase, model_class: Type[T]):
        """
        Initialize repository.
        
        Args:
            database: MongoDB database instance
            model_class: Pydantic model class for the collection
        """
        self.database = database
        self.model_class = model_class
        self.collection_name = self._get_collection_name()
        self.collection: AsyncIOMotorCollection = database[self.collection_name]
        
    @abstractmethod
    def _get_collection_name(self) -> str:
        """Return the collection name for this repository."""
        pass
        
    async def create(self, document: T) -> T:
        """
        Create a new document.
        
        Args:
            document: Document to create
            
        Returns:
            Created document (Pydantic model instance)
        """
        try:
            # For Pydantic V2, use model_dump instead of dict
            document_dict = document.model_dump(by_alias=True)  # exclude_unset defaults to False
            
            # If _id is part of the model and is None (e.g. from default_factory but not yet set),
            # Pydantic might include it as None. Motor typically expects _id to be absent for auto-generation
            # or present with a value.
            if "_id" in document_dict and document_dict["_id"] is None:
                document_dict.pop("_id")
            # No need to explicitly handle document.id here if model_dump(by_alias=True) correctly maps 'id' to '_id'.
            # If 'id' is a PyObjectId and already generated, it will be included (and possibly stringified by json_encoders
            # if model_dump is used for serialization to JSON, but here it's for a Python dict for Motor).

            result = await self.collection.insert_one(document_dict)
            
            # Fetch the newly created document by its ID to return the full model instance
            # The type of result.inserted_id will be ObjectId if _id was not in document_dict, 
            # or the type of document_dict["_id"] if it was present.
            # find_by_id expects an ObjectId.
            inserted_id = result.inserted_id
            if not isinstance(inserted_id, ObjectId):
                # This can happen if _id was a string in document_dict (e.g. from a model_dump with json_encoders)
                # However, PyObjectId's __get_pydantic_core_schema__ should ensure it's an ObjectId in the model instance.
                # If model_dump(by_alias=True) converts PyObjectId to string for _id, then find_by_id needs to handle string IDs
                # or we ensure inserted_id is always ObjectId here.
                # For now, assume find_by_id correctly handles the type of ID it receives or that inserted_id is ObjectId.
                # Let's assume result.inserted_id is compatible with find_by_id's ObjectId requirement.
                pass # If find_by_id strictly needs ObjectId, conversion might be needed if inserted_id is str.

            created_document = await self.find_by_id(inserted_id)
            if created_document is None:
                # This should ideally not happen if insert_one succeeded and find_by_id is correct
                raise Exception(f"Failed to retrieve document after insertion with id {result.inserted_id}")
            return created_document
            
        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {e}")
            raise
            
    async def find_by_id(self, document_id: ObjectId) -> Optional[T]:
        """
        Find document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        try:
            document = await self.collection.find_one({"_id": document_id})
            if document:
                return self.model_class(**document)
            return None
            
        except Exception as e:
            logger.error(f"Error finding document by ID in {self.collection_name}: {e}")
            raise

    async def find_many(self, filter_dict: Dict[str, Any] = None, 
                       limit: Optional[int] = None, 
                       skip: Optional[int] = None) -> List[T]:
        """
        Find multiple documents.
        
        Args:
            filter_dict: Filter criteria
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            
        Returns:
            List of documents
        """
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict)
            
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            documents = await cursor.to_list(length=limit)
            return [self.model_class(**doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Error finding documents in {self.collection_name}: {e}")
            raise

    async def update_by_id(self, document_id: ObjectId, update_data: Dict[str, Any]) -> bool:
        """
        Update document by ID.
        
        Args:
            document_id: Document ID
            update_data: Update data
            
        Returns:
            True if document was updated, False otherwise
        """
        try:
            result = await self.collection.update_one(
                {"_id": document_id}, 
                {"$set": update_data}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {e}")
            raise

    async def delete_by_id(self, document_id: ObjectId) -> bool:
        """
        Delete document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one({"_id": document_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document in {self.collection_name}: {e}")
            raise
