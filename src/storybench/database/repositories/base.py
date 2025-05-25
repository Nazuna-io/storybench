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
            Created document with ID
        """
        try:
            document_dict = document.dict(by_alias=True, exclude_unset=True)
            
            # Remove None _id if present
            if document_dict.get("_id") is None:
                document_dict.pop("_id", None)
                
            result = await self.collection.insert_one(document_dict)
            
            # Update document with new ID
            document_dict["_id"] = result.inserted_id
            return self.model_class(**document_dict)
            
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
