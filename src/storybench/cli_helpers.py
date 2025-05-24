"""Helper functions for CLI operations."""

import click
from tqdm import tqdm
from typing import Dict, List


async def _process_model(evaluator, cfg, tracker, config_hash, sequences, prompts_per_sequence):
    """Process all tasks for a single model."""
    model_name = evaluator.name
    
    # Get next task to resume from
    next_task = tracker.get_next_task(
        model_name, config_hash, sequences, 
        cfg.global_settings.num_runs, prompts_per_sequence
    )
    
    if next_task is None:
        click.echo(f"✓ {model_name} already complete")
        return
        
    # Calculate total remaining tasks
    total_tasks = sum(len(prompts) * cfg.global_settings.num_runs 
                     for prompts in cfg.prompts.values())
    
    with tqdm(total=total_tasks, desc=f"Evaluating {model_name}") as pbar:
        
        for sequence in sequences:
            prompts = cfg.prompts[sequence]
            
            for run in range(1, cfg.global_settings.num_runs + 1):
                
                for prompt_idx, prompt_data in enumerate(prompts):
                    
                    # Skip if already completed
                    if (sequence, run, prompt_idx) < next_task:
                        pbar.update(1)
                        continue
                        
                    # Generate response
                    response = await evaluator.generate_response(
                        prompt_data["text"],
                        temperature=cfg.global_settings.temperature,
                        max_tokens=cfg.global_settings.max_tokens
                    )
                    
                    # Add prompt text to response
                    response["prompt_text"] = prompt_data["text"]
                    
                    # Save response
                    tracker.save_response(
                        model_name, config_hash, sequence, 
                        run, prompt_idx, prompt_data["name"], response
                    )
                    
                    pbar.update(1)
                    
                    # Show progress
                    if not response.get("metadata", {}).get("error"):
                        click.echo(f"  ✓ {sequence} run {run} - {prompt_data['name']}")
                    else:
                        click.echo(f"  ✗ {sequence} run {run} - {prompt_data['name']} (Error)")
