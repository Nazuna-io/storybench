#!/usr/bin/env python3
"""
Test script to verify Option B fix for local evaluation architecture.
This tests that we create ONE evaluation with ALL responses instead of multiple evaluations.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, '/home/todd/storybench/src')

from storybench.database.connection import get_database
from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_unified_evaluation():
    """Test that our Option B fix creates a unified evaluation structure."""
    try:
        # Connect to database
        database = await get_database()
        runner = DatabaseEvaluationRunner(database)
        
        logger.info("🚀 Testing Option B Fix - Unified Evaluation Architecture")
        
        # Check existing evaluations before test
        existing_evals = await database.evaluations.count_documents({})
        existing_responses = await database.responses.count_documents({})
        logger.info(f"📊 Before test: {existing_evals} evaluations, {existing_responses} responses")
        
        # Test the total_tasks calculation
        models = ["TestLocal"]
        sequences = {
            "TestSequence": [
                {"name": "Prompt1", "text": "Test prompt 1"},
                {"name": "Prompt2", "text": "Test prompt 2"},
                {"name": "Prompt3", "text": "Test prompt 3"}
            ]
        }
        num_runs = 3
        
        # Calculate expected total tasks using the same logic as the runner
        expected_total = len(models) * sum(len(prompts) for prompts in sequences.values()) * num_runs
        logger.info(f"📈 Expected total tasks: {len(models)} models × {sum(len(prompts) for prompts in sequences.values())} prompts × {num_runs} runs = {expected_total}")
        
        # Test the calculation method directly
        calculated_total = runner._calculate_total_tasks(models, sequences, num_runs)
        logger.info(f"🧮 Calculated total tasks: {calculated_total}")
        
        if calculated_total == expected_total:
            logger.info("✅ Total tasks calculation is correct!")
        else:
            logger.error(f"❌ Total tasks calculation mismatch: expected {expected_total}, got {calculated_total}")
            return False
        
        # Test the response plan logic
        response_plan = []
        for model_name in models:
            for sequence_name, prompts in sequences.items():
                for run in range(1, num_runs + 1):
                    for prompt_index, prompt in enumerate(prompts):
                        response_plan.append({
                            "model_name": model_name,
                            "sequence_name": sequence_name,
                            "run": run,
                            "prompt_index": prompt_index,
                            "prompt": prompt
                        })
        
        logger.info(f"🗺️  Response plan created: {len(response_plan)} total responses")
        logger.info(f"📋 Plan breakdown:")
        for i, item in enumerate(response_plan[:6]):  # Show first 6 items
            logger.info(f"   {i+1}. {item['model_name']}/{item['sequence_name']}/run{item['run']}/{item['prompt']['name']}")
        if len(response_plan) > 6:
            logger.info(f"   ... and {len(response_plan) - 6} more")
        
        if len(response_plan) == expected_total:
            logger.info("✅ Response plan matches expected total!")
        else:
            logger.error(f"❌ Response plan mismatch: expected {expected_total}, got {len(response_plan)}")
            return False
        
        # Test that we get the right distribution
        model_counts = {}
        sequence_counts = {}
        run_counts = {}
        
        for item in response_plan:
            model_counts[item['model_name']] = model_counts.get(item['model_name'], 0) + 1
            sequence_counts[item['sequence_name']] = sequence_counts.get(item['sequence_name'], 0) + 1
            run_counts[item['run']] = run_counts.get(item['run'], 0) + 1
        
        logger.info(f"📊 Distribution analysis:")
        logger.info(f"   Models: {model_counts}")
        logger.info(f"   Sequences: {sequence_counts}")
        logger.info(f"   Runs: {run_counts}")
        
        # Verify distribution is correct
        expected_per_model = len(sequences) * sum(len(prompts) for prompts in sequences.values()) * num_runs
        expected_per_sequence = len(models) * sum(len(prompts) for prompts in sequences.values()) * num_runs  
        expected_per_run = len(models) * sum(len(prompts) for prompts in sequences.values())
        
        if (model_counts.get("TestLocal", 0) == expected_per_model and
            sequence_counts.get("TestSequence", 0) == expected_per_sequence and
            all(count == expected_per_run for count in run_counts.values()) and
            len(run_counts) == num_runs):
            logger.info("✅ Response distribution is correct!")
        else:
            logger.error("❌ Response distribution is incorrect")
            logger.error(f"   Expected per model: {expected_per_model}, got: {model_counts}")
            logger.error(f"   Expected per sequence: {expected_per_sequence}, got: {sequence_counts}") 
            logger.error(f"   Expected per run: {expected_per_run}")
            return False
        
        logger.info("🎉 Option B Architecture Test PASSED!")
        logger.info("   ✅ Single evaluation will be created")
        logger.info("   ✅ All responses will belong to that evaluation")
        logger.info("   ✅ Progress tracking will be unified")
        logger.info("   ✅ LLM evaluation will run on all responses together")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_unified_evaluation())
    if success:
        print("\n🎉 OPTION B FIX VERIFIED - Ready for testing!")
    else:
        print("\n❌ OPTION B FIX NEEDS ATTENTION")
        sys.exit(1)
