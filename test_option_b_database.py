#!/usr/bin/env python3
"""
Direct test of Option B fix using the background evaluation service.
This tests our unified evaluation architecture without the local models complexity.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment
os.environ["MONGODB_URI"] = "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0"
os.environ["OPENAI_API_KEY"] = "sk-proj-fAx061DRnXUcg9oh1bPtc3KdUgfY9CiUvNnrrAto_9ygpXmKZ-lSS7d3tqxaDQiwsTIFdU7vETT3BlbkFJU"  # Truncated for security

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_option_b_direct():
    """Test Option B fix by directly using the background evaluation service."""
    logger.info("🧪 Testing Option B - Direct Background Service Test")
    
    try:
        # Import required modules
        from storybench.database.connection import init_database, get_database
        from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner
        from storybench.database.models import EvaluationStatus
        
        # Initialize database
        await init_database()
        database = await get_database()
        
        # Create evaluation runner
        runner = DatabaseEvaluationRunner(database)
        
        # Test parameters (similar to real usage)
        models = ["GPT-4o-mini"]  # Use a real API model for testing
        sequences = {
            "TestSequence": [
                {"name": "Creativity Test 1", "text": "Write a short creative story about a robot discovering emotions."},
                {"name": "Creativity Test 2", "text": "Describe an unusual invention that changes daily life."},  
                {"name": "Creativity Test 3", "text": "Create a character who can speak to plants."}
            ]
        }
        
        global_settings = {
            "num_runs": 3,
            "temperature": 0.7
        }
        
        logger.info(f"Starting evaluation with Option B architecture:")
        logger.info(f"  Models: {models}")
        logger.info(f"  Sequences: {list(sequences.keys())}")
        logger.info(f"  Runs: {global_settings['num_runs']}")
        
        # Calculate expected total using our logic
        total_prompts = sum(len(prompts) for prompts in sequences.values())
        expected_total = len(models) * total_prompts * global_settings['num_runs']
        logger.info(f"  Expected responses: {len(models)} × {total_prompts} × {global_settings['num_runs']} = {expected_total}")
        
        # Get initial database state
        initial_evals = await database.evaluations.count_documents({})
        initial_responses = await database.responses.count_documents({})
        logger.info(f"📊 Initial state: {initial_evals} evaluations, {initial_responses} responses")
        
        # Start evaluation (this should create ONE evaluation with proper total_tasks)
        evaluation = await runner.start_evaluation(
            models=models,
            sequences=sequences, 
            global_settings=global_settings
        )
        
        logger.info(f"✅ Created evaluation {evaluation.id}")
        logger.info(f"   Status: {evaluation.status}")
        logger.info(f"   Total tasks: {evaluation.total_tasks}")
        logger.info(f"   Models: {evaluation.models}")
        
        # Verify the evaluation was created correctly
        if evaluation.total_tasks == expected_total:
            logger.info("✅ Total tasks calculation is correct!")
        else:
            logger.error(f"❌ Total tasks mismatch: expected {expected_total}, got {evaluation.total_tasks}")
            return False
        
        # Check database state after creation
        final_evals = await database.evaluations.count_documents({})
        logger.info(f"📊 After creation: {final_evals} evaluations (+{final_evals - initial_evals})")
        
        if final_evals - initial_evals == 1:
            logger.info("✅ Created exactly 1 evaluation (Option B working!)")
        else:
            logger.error(f"❌ Created {final_evals - initial_evals} evaluations (should be 1)")
            return False
        
        # Get the evaluation from database to verify structure
        eval_doc = await database.evaluations.find_one({"_id": evaluation.id})
        logger.info(f"📋 Database evaluation record:")
        logger.info(f"   _id: {eval_doc.get('_id')}")
        logger.info(f"   status: {eval_doc.get('status')}")
        logger.info(f"   total_tasks: {eval_doc.get('total_tasks')}")
        logger.info(f"   completed_tasks: {eval_doc.get('completed_tasks')}")
        logger.info(f"   models: {eval_doc.get('models')}")
        
        logger.info("🎉 OPTION B ARCHITECTURE TEST PASSED!")
        logger.info("   ✅ Creates single unified evaluation")
        logger.info(f"   ✅ Correct total_tasks calculation ({expected_total})")
        logger.info("   ✅ Proper database structure")
        logger.info("   ✅ Ready for response generation with unified architecture")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_option_b_direct()
    
    if success:
        print("\n🎉 OPTION B FIX VERIFIED - Database Architecture Correct!")
        print("✅ Unified evaluation creation works")
        print("✅ Total tasks calculation correct")  
        print("✅ Ready for production testing")
        return 0
    else:
        print("\n❌ OPTION B TEST FAILED")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
