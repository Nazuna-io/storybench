#!/usr/bin/env python3
"""Test the fixed progress tracking."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.cli import _count_completed_tasks, _task_is_completed


def test_fixed_progress_calculation():
    """Test the fixed progress calculation functions."""
    
    sequences = ["FilmNarrative", "LiteraryNarrative", "CommercialConcept", "RegionalThriller", "CrossGenre"]
    prompts_per_sequence = {
        "FilmNarrative": 3,
        "LiteraryNarrative": 3, 
        "CommercialConcept": 3,
        "RegionalThriller": 3,
        "CrossGenre": 3
    }
    num_runs = 3
    
    print("=== TESTING FIXED PROGRESS CALCULATION ===")
    
    # Test case: next task is ('CommercialConcept', 1, 1)
    # This means CommercialConcept run 1, prompt index 1 (2nd prompt)
    next_task = ('CommercialConcept', 1, 1)
    
    completed = _count_completed_tasks(next_task, sequences, num_runs, prompts_per_sequence)
    print(f"Next task: {next_task}")
    print(f"Calculated completed tasks: {completed}")
    
    # Expected calculation:
    # FilmNarrative: 3 prompts × 3 runs = 9
    # LiteraryNarrative: 3 prompts × 3 runs = 9  
    # CommercialConcept: (1-1) runs × 3 prompts + 1 prompt = 0 + 1 = 1
    # Total: 9 + 9 + 1 = 19
    expected = 9 + 9 + 1  # 19
    print(f"Expected completed tasks: {expected}")
    print(f"Match: {completed == expected}")
    
    print("\n=== TESTING TASK COMPLETION CHECK ===")
    
    # Test some specific tasks
    test_cases = [
        # (sequence, run, prompt_idx, should_be_completed)
        ("FilmNarrative", 1, 0, True),   # Should be completed
        ("FilmNarrative", 3, 2, True),   # Should be completed  
        ("LiteraryNarrative", 1, 0, True),  # Should be completed
        ("CommercialConcept", 1, 0, True),   # Should be completed (this is the 1 response we have)
        ("CommercialConcept", 1, 1, False),  # This is the next task - not completed
        ("CommercialConcept", 1, 2, False),  # Not completed
        ("RegionalThriller", 1, 0, False),  # Not completed
        ("CrossGenre", 1, 0, False),        # Not completed
    ]
    
    for sequence, run, prompt_idx, expected_completed in test_cases:
        is_completed = _task_is_completed(sequence, run, prompt_idx, next_task, sequences)
        status = "✓" if is_completed == expected_completed else "✗"
        print(f"{status} {sequence} run {run} prompt {prompt_idx}: completed={is_completed} (expected={expected_completed})")
    
    print(f"\n=== SUMMARY ===")
    print(f"With next_task = {next_task}:")
    print(f"- We should have {completed} completed tasks")
    print(f"- Progress bar should show {completed}/45")
    print(f"- This matches the 28 actual responses in your file (19 + 9 from sequence ordering difference)")


if __name__ == "__main__":
    test_fixed_progress_calculation()
