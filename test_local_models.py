#!/usr/bin/env python3
"""Test local model functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.web.services.local_model_service import LocalModelService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_local_model_service():
    """Test the local model service functionality."""
    print("=== Testing Local Model Service ===")
    
    # Initialize service without database for testing
    service = LocalModelService(database=None)
    
    # Test configuration loading
    print("\n1. Testing configuration loading...")
    config = await service.load_configuration()
    print(f"Loaded config: {config}")
    
    # Test hardware info
    print("\n2. Testing hardware information...")
    hardware_info = await service.get_hardware_info()
    print(f"Hardware info: {hardware_info}")
    
    # Test configuration saving
    print("\n3. Testing configuration saving...")
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
        "use_local_evaluator": True,
        "settings": {
            "temperature": 1.0,
            "max_tokens": 512,
            "num_runs": 1,
            "vram_limit_percent": 80,
            "auto_evaluate": True
        }
    }
    
    try:
        await service.save_configuration(test_config)
        print("Configuration saved successfully")
    except Exception as e:
        print(f"Error saving configuration: {e}")
    
    # Test small evaluation run
    print("\n4. Testing small evaluation run...")
    try:
        # Register console callback to see output
        console_messages = []
        
        def console_callback(message, message_type="info"):
            console_messages.append(f"[{message_type}] {message}")
            print(f"[{message_type}] {message}")
        
        service.register_output_callback(console_callback)
        
        # Run a small test evaluation
        await service.run_local_evaluation(
            generation_model=test_config["generation_model"],
            evaluation_model=test_config["evaluation_model"],
            use_local_evaluator=False,  # Use API evaluator for now
            sequences=["FilmNarrative"],  # Just one sequence
            settings={
                **test_config["settings"],
                "num_runs": 1,  # Just one run
                "max_tokens": 100  # Small response
            },
            api_keys={}  # No API keys for this test
        )
        
        print("\n=== Console Messages ===")
        for msg in console_messages:
            print(msg)
            
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_local_model_service())
