#!/usr/bin/env python3
"""
Test Phase 2.0 Parallel Evaluation System

This script tests the new sequence-level parallelization with a small subset
to validate the implementation before running full-scale evaluations.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import init_database
from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner
from storybench.evaluators.api_evaluator import APIEvaluator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_parallel_evaluation():
    """Test parallel evaluation with a small subset."""
    
    print("Phase 2.0 Parallel Evaluation Test")
    print("=" * 50)
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY required for test")
        return False
    
    try:
        # Initialize database
        print("1. Initializing database...")
        database = await init_database()
        print("✅ Database connected")
        
        # Initialize evaluation runner with parallel support
        print("2. Initializing parallel evaluation runner...")
        evaluation_runner = DatabaseEvaluationRunner(database, enable_parallel=True)
        print("✅ Parallel runner initialized")
        
        # Test configuration: 2 models, 2 sequences for quick validation
        test_models = [
            {
                "name": "gpt-4o-test",
                "model_id": "gpt-4o",
                "max_tokens": 128000,
                "provider": "openai"
            }
        ]
        
        # Subset of sequences for testing (2 out of 5)
        test_sequences = {
            "FilmNarrative": [
                {"name": "Initial Concept", "text": "Create a short film concept about the future."},
                {"name": "Scene Development", "text": "Develop a key scene from your concept."},
                {"name": "Visual Realization", "text": "Describe the most striking visual moment."}
            ],
            "LiteraryNarrative": [
                {"name": "Initial Concept", "text": "Outline a short story about survival."},
                {"name": "Character Development", "text": "Write a character development scene."},
                {"name": "Visual Moment", "text": "Describe the most emotional visual moment."}
            ]
        }
        
        print("3. Starting test evaluation...")
        print("Expected: 1 model × 2 sequences × 3 prompts × 2 runs = 12 total API calls")
        print("Parallelization: 2 sequences running concurrently")
        
        # Start evaluation
        evaluation = await evaluation_runner.start_evaluation(
            models=[model["name"] for model in test_models],
            sequences=test_sequences,
            criteria={"test": True},
            global_settings={"num_runs": 2}  # Reduced runs for testing
        )
        
        evaluation_id = str(evaluation.id)
        print(f"✅ Evaluation created: {evaluation_id}")
        
        # Create evaluator factory
        def create_evaluator(model_config):
            return APIEvaluator(
                model_name=model_config["model_id"],
                api_key=openai_key,
                provider="openai"
            )
        
        start_time = datetime.now()
        
        # Run parallel evaluation
        results = await evaluation_runner.run_parallel_evaluation(
            evaluation_id=evaluation_id,
            models=test_models,
            sequences=test_sequences,
            num_runs=2,
            evaluator_factory=create_evaluator
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 50)
        print("PARALLEL EVALUATION RESULTS")
        print("=" * 50)
        
        if results.get("success", False):
            print("✅ Parallel evaluation completed successfully!")
            print(f"Duration: {duration:.1f} seconds")
            print(f"Workers: {results['successful_workers']}/{results['total_workers']}")
            return True
        else:
            print("❌ Parallel evaluation failed!")
            print(f"Error: {results.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner."""
    success = await test_parallel_evaluation()
    
    if success:
        print("\n🎉 Phase 2.0 parallel evaluation test completed successfully!")
        print("Ready for full-scale parallel evaluations with 5x speedup.")
    else:
        print("\n💥 Phase 2.0 test failed. Check logs for details.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
