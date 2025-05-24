"""Repository package for data access abstraction."""

from .base import Repository
from .file_repository import FileRepository

__all__ = ["Repository", "FileRepository"]
