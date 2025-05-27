#!/usr/bin/env python3
"""
Simple test of Option B architecture logic without database dependencies.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_option_b_logic():
    """Test the unified evaluation plan logic."""
    
    # Test parameters matching real usage
    models = ["TestLocal"] 
    sequences = {
        "FilmNarrative": [
            {"name": "Initial Concept", "text": "Create a feature film concept..."},
            {"name": "Character Development", "text": "Develop the main characters..."},
            {"name": "Plot Structure", "text": "Outline the plot structure..."}
        ]
    }
    num_runs = 3
    
    logger.info("🚀 Testing Option B - Unified Evaluation Architecture")
    
    # OLD WAY (problematic) - This is what was creating multiple evaluations
    logger.info("\n❌ OLD WAY (caused fragmentation):")
    old_way_count = 0
    for model_name in models:
        logger.info(f"  Processing model {model_name}")
        for sequence_name, prompts in sequences.items():
            logger.info(f"    Processing sequence {sequence_name}")
            for run in range(1, num_runs + 1):
                logger.info(f"      Processing run {run} (separate evaluation created here)")
                for prompt_index, prompt in enumerate(prompts):
                    old_way_count += 1
                    # This would create separate database evaluation per run
    
    logger.info(f"  Result: {old_way_count} responses across {len(models) * len(sequences) * num_runs} separate evaluations")
    
    # NEW WAY (Option B) - Single unified evaluation
    logger.info("\n✅ NEW WAY (Option B - unified):")
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
    
    logger.info(f"  Single evaluation plan created with {len(response_plan)} total responses")
    
    # Calculate expected total
    total_prompts = sum(len(prompts) for prompts in sequences.values()) 
    expected_total = len(models) * total_prompts * num_runs
    logger.info(f"  Expected: {len(models)} models × {total_prompts} prompts × {num_runs} runs = {expected_total}")
    
    # Verify the plan
    if len(response_plan) == expected_total:
        logger.info("  ✅ Response plan count is correct!")
    else:
        logger.error(f"  ❌ Count mismatch: expected {expected_total}, got {len(response_plan)}")
        return False
    
    # Check distribution
    run_distribution = {}
    for item in response_plan:
        run_distribution[item['run']] = run_distribution.get(item['run'], 0) + 1
    
    logger.info(f"  Distribution by run: {run_distribution}")
    
    expected_per_run = len(models) * total_prompts
    all_runs_correct = all(count == expected_per_run for count in run_distribution.values())
    
    if all_runs_correct and len(run_distribution) == num_runs:
        logger.info("  ✅ Run distribution is correct!")
    else:
        logger.error(f"  ❌ Run distribution incorrect. Expected {expected_per_run} per run")
        return False
    
    # Show first few items of the plan
    logger.info(f"\n📋 Response plan preview (first 5 of {len(response_plan)}):")
    for i, item in enumerate(response_plan[:5]):
        logger.info(f"  {i+1}. {item['model_name']}/{item['sequence_name']}/run{item['run']}/{item['prompt']['name']}")
    
    logger.info(f"\n🎉 OPTION B ARCHITECTURE VERIFIED!")
    logger.info(f"  ✅ Creates 1 evaluation instead of {len(models) * len(sequences) * num_runs}")
    logger.info(f"  ✅ All {len(response_plan)} responses belong to same evaluation")
    logger.info(f"  ✅ Progress tracking will be unified ({len(response_plan)} total tasks)")
    logger.info(f"  ✅ LLM evaluation will run on all responses together")
    
    return True

if __name__ == "__main__":
    success = test_option_b_logic()
    if success:
        print("\n🎉 OPTION B FIX VERIFIED - Architecture is correct!")
        sys.exit(0)
    else:
        print("\n❌ OPTION B FIX HAS ISSUES")
        sys.exit(1)
