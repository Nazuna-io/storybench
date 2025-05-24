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
        
    # Calculate total and remaining tasks
    total_tasks = sum(len(prompts) * cfg.global_settings.num_runs 
                     for prompts in cfg.prompts.values())
    
    # Calculate completed tasks
    completed_tasks = _count_completed_tasks(next_task, sequences, cfg.global_settings.num_runs, prompts_per_sequence)
    remaining_tasks = total_tasks - completed_tasks
    
    click.echo(f"Resuming {model_name}: {completed_tasks}/{total_tasks} completed, {remaining_tasks} remaining")
    
    with tqdm(total=total_tasks, initial=completed_tasks, desc=f"Evaluating {model_name}") as pbar:
        
        for sequence in sequences:
            prompts = cfg.prompts[sequence]
            
            for run in range(1, cfg.global_settings.num_runs + 1):
                
                for prompt_idx, prompt_data in enumerate(prompts):
                    
                    # Skip if already completed
                    if _task_is_completed(sequence, run, prompt_idx, next_task, sequences):
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


def _count_completed_tasks(next_task, sequences, num_runs, prompts_per_sequence):
    """Count how many tasks should be completed before the next_task."""
    if next_task is None:
        return sum(prompts_per_sequence[seq] * num_runs for seq in sequences)
    
    next_seq, next_run, next_prompt_idx = next_task
    completed = 0
    
    for sequence in sequences:
        if sequence == next_seq:
            # Add completed runs in this sequence
            completed += (next_run - 1) * prompts_per_sequence[sequence]
            # Add completed prompts in current run
            completed += next_prompt_idx
            break
        else:
            # Add all tasks from completed sequences
            completed += prompts_per_sequence[sequence] * num_runs
    
    return completed


def _task_is_completed(sequence, run, prompt_idx, next_task, sequences):
    """Check if a task is already completed."""
    if next_task is None:
        return True  # All tasks completed
    
    next_seq, next_run, next_prompt_idx = next_task
    
    # Find sequence index
    try:
        seq_idx = sequences.index(sequence)
        next_seq_idx = sequences.index(next_seq)
    except ValueError:
        return False
    
    # Compare sequence, run, prompt in order
    if seq_idx < next_seq_idx:
        return True
    elif seq_idx > next_seq_idx:
        return False
    else:  # Same sequence
        if run < next_run:
            return True
        elif run > next_run:
            return False
        else:  # Same run
            return prompt_idx < next_prompt_idx