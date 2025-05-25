"""Database module for MongoDB Atlas integration."""

from .connection import get_database, init_database, close_database
from .models import *

__all__ = [
    "get_database",
    "init_database", 
    "close_database",
]
