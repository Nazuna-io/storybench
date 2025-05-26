#!/usr/bin/env python3
"""Test local model functionality with proper database initialization."""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variable for database
os.environ.setdefault("MONGODB_URI", "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")

from storybench.web.services.local_model_service import LocalModelService
from storybench.database.connection import init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_local_model_with_proper_database():
    """Test the local model service functionality with proper database initialization."""
    print("=== Testing Local Model Service with Proper Database ===")
    
    # Initialize database connection properly
    try:
        database = await init_database()
        print("Database connection and initialization successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        database = None
    
    # Initialize service with database
    service = LocalModelService(database=database)
    
    # Test configuration loading
    print("\n1. Testing configuration loading...")
    config = await service.load_configuration()
    print(f"Config loaded successfully")
    
    # Test small evaluation run
    print("\n2. Testing small evaluation run with database...")
    try:
        # Register console callback to see output
        console_messages = []
        
        def console_callback(message, message_type="info"):
            console_messages.append(f"[{message_type}] {message}")
            print(f"[{message_type}] {message}")
        
        service.register_output_callback(console_callback)
        
        test_config = {
            "generation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "evaluation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "use_local_evaluator": False,
            "settings": {
                "temperature": 1.0,
                "max_tokens": 100,
                "num_runs": 1,
                "vram_limit_percent": 80,
                "auto_evaluate": False  # Skip evaluation for this test
            }
        }
        
        # API keys from environment
        api_keys = {
            "openai": os.environ.get("OPENAI_API_KEY", ""),
            "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
            "google": os.environ.get("GOOGLE_API_KEY", "")
        }
        
        # Run a small test evaluation
        await service.run_local_evaluation(
            generation_model=test_config["generation_model"],
            evaluation_model=test_config["evaluation_model"],
            use_local_evaluator=False,  # Use API evaluator
            sequences=["FilmNarrative"],  # Just one sequence
            settings=test_config["settings"],
            api_keys=api_keys
        )
        
        print("\n=== Final Console Messages ===")
        for msg in console_messages[-5:]:  # Show last 5 messages
            print(msg)
            
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_local_model_with_proper_database())
