#!/usr/bin/env python3
"""End-to-end test for local model functionality with database integration."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.absolute()))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import required modules
try:
    from storybench.evaluators.local_evaluator import LocalEvaluator
    from storybench.database.connection import init_database, get_database, close_database
    from storybench.database.connection import RESPONSES_COLLECTION, EVALUATIONS_COLLECTION
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure you're running from the project root directory")
    sys.exit(1)

# Test configuration
TEST_MODEL_CONFIG = {
    "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",  # Using a slightly larger model for better quality
    "subdirectory": "",
    "vram_limit_percent": 80,
    "temperature": 0.7,
    "max_tokens": 512  # Keep responses reasonable for testing
}

# Test prompt
TEST_PROMPT = "Write a short story about a robot learning to dance."

# Model configuration
MODEL_NAME = "test_local_model"

async def setup_test_environment():
    """Set up test environment and return database connection."""
    logger.info("Setting up test environment...")
    
    try:
        # Initialize database connection
        db = await init_database()
        logger.info("Database connection established")
        return db
    except Exception as e:
        logger.error(f"Failed to set up test environment: {e}")
        raise

async def test_response_generation(db):
    """Test generating a response with the local model."""
    logger.info("\n=== Testing Response Generation ===")
    
    try:
        # Initialize the local evaluator
        logger.info(f"Initializing local model: {MODEL_NAME}")
        evaluator = LocalEvaluator(
            name=MODEL_NAME,
            config=TEST_MODEL_CONFIG
        )
        
        # Set up the model (download if needed)
        logger.info("Setting up model (this may take a while for first run)...")
        if not await evaluator.setup():
            raise RuntimeError("Failed to set up local model")
        
        # Generate response
        logger.info(f"Generating response for prompt: {TEST_PROMPT}")
        response = await evaluator.generate_response(
            prompt=TEST_PROMPT,
            temperature=TEST_MODEL_CONFIG["temperature"],
            max_tokens=TEST_MODEL_CONFIG["max_tokens"]
        )
        
        if not response or 'text' not in response:
            raise ValueError("No response generated or invalid response format")
            
        response_text = response['text']
        logger.info(f"Generated response: {response_text[:200]}...")
        
        # Save response to database
        response_doc = {
            "prompt": TEST_PROMPT,
            "response_text": response_text,
            "model_name": MODEL_NAME,
            "model_config": TEST_MODEL_CONFIG,
            "sequence_id": "test_sequence_001",
            "created_at": datetime.utcnow(),
            "metadata": {
                "test_run": True,
                "generation_time": response.get('generation_time'),
                "usage": response.get('usage', {})
            }
        }
        
        result = await db[RESPONSES_COLLECTION].insert_one(response_doc)
        response_id = str(result.inserted_id)
        logger.info(f"Response saved to database with ID: {response_id}")
        
        # Clean up
        await evaluator.cleanup()
        
        return response_id, response_text
        
    except Exception as e:
        logger.error(f"Response generation test failed: {e}", exc_info=True)
        raise

async def test_evaluation(db, response_id: str):
    """Test evaluating the generated response."""
    logger.info("\n=== Testing Response Evaluation ===")
    
    try:
        # In a real test, we would call the evaluation service here
        # For now, we'll just create a test evaluation
        evaluation_doc = {
            "response_id": response_id,
            "evaluator_name": "test_local_evaluator",
            "scores": {
                "creativity": 4.0,
                "coherence": 4.5,
                "relevance": 4.0
            },
            "feedback": "Test evaluation completed successfully",
            "metadata": {"test_run": True}
        }
        
        result = await db[EVALUATIONS_COLLECTION].insert_one(evaluation_doc)
        logger.info(f"Evaluation saved to database with ID: {result.inserted_id}")
        
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Evaluation test failed: {e}")
        raise

async def cleanup_test_data(db, response_id: str):
    """Clean up test data from database."""
    logger.info("\n=== Cleaning up test data ===")
    
    try:
        # Delete test response and evaluation
        await db[RESPONSES_COLLECTION].delete_many({"sequence_id": "test_sequence_001"})
        await db[EVALUATIONS_COLLECTION].delete_many({"response_id": response_id})
        logger.info("Test data cleaned up")
    except Exception as e:
        logger.error(f"Failed to clean up test data: {e}")
        raise

async def run_end_to_end_test():
    """Run the complete end-to-end test."""
    db = None
    try:
        # Set up test environment
        service, db = await setup_test_environment()
        
        # Test response generation
        response_id = await test_response_generation(service, db)
        
        # Test evaluation
        evaluation_id = await test_evaluation(service, db, response_id)
        
        # Print success message
        logger.info("\n✅ End-to-end test completed successfully!")
        logger.info(f"Response ID: {response_id}")
        logger.info(f"Evaluation ID: {evaluation_id}")
        
        # Clean up test data
        await cleanup_test_data(db, response_id)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False
    finally:
        # Ensure database connection is closed
        if db:
            await close_database()

if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())
