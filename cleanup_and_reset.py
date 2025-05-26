#!/usr/bin/env python3
"""
Comprehensive cleanup and reset script for Storybench.
This script will:
1. Delete all responses, evaluations, and LLM evaluations from the database
2. Update API keys from .env file with proper encryption
3. Verify the cleanup was successful
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from storybench.database.connection import init_database
from cryptography.fernet import Fernet
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def cleanup_database():
    """Delete all evaluation data from the database."""
    logger.info("🧹 Starting database cleanup...")
    
    try:
        db = await init_database()
        
        # Collections to clean up
        collections_to_cleanup = [
            'responses',
            'evaluations', 
            'response_llm_evaluations'
        ]
        
        total_deleted = 0
        
        for collection_name in collections_to_cleanup:
            collection = db[collection_name]
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            logger.info(f"📊 {collection_name}: {count_before} documents found")
            
            if count_before > 0:
                # Delete all documents
                result = await collection.delete_many({})
                deleted_count = result.deleted_count
                total_deleted += deleted_count
                logger.info(f"🗑️  {collection_name}: Deleted {deleted_count} documents")
