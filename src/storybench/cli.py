"""Main CLI interface for storybench."""

import asyncio
import click
import os
from pathlib import Path
from dotenv import load_dotenv
from .models.config import Config
from .models.progress import ProgressTracker
from .evaluators.factory import EvaluatorFactory
from tqdm import tqdm


@click.group()
def cli():
    """StorybenchLLM - Evaluate creativity of LLMs across various writing tasks."""
    pass


@cli.command()
@click.option('--config', '-c', default='config/models.yaml', 
              help='Path to configuration file')
@click.option('--dry-run', is_flag=True, help='Validate configuration without running')
@click.option('--resume', is_flag=True, help='Resume from previous incomplete run')
def evaluate(config, dry_run, resume):
    """Run LLM creativity evaluation."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Load configuration
        click.echo(f"Loading configuration from {config}")
        cfg = Config.load_config(config)
        
        # Validate configuration
        errors = cfg.validate()
        if errors:
            click.echo("Configuration errors:")
            for error in errors:
                click.echo(f"  - {error}")
            return
            
        click.echo(f"✓ Configuration valid - {len(cfg.models)} models, {len(cfg.prompts)} prompt sequences")
        
        if dry_run:
            click.echo("Dry run complete - configuration is valid")
            return
            
        # Check API keys
        api_keys = _get_api_keys()
        missing_keys = _check_required_api_keys(cfg.models, api_keys)
        if missing_keys:
            click.echo("Missing required API keys:")
            for key in missing_keys:
                click.echo(f"  - {key}")
            click.echo("Please set these in your .env file")
            return
            
        # Run evaluation
        asyncio.run(_run_evaluation(cfg, api_keys, resume))
        
    except Exception as e:
        click.echo(f"Error: {e}")



@cli.command()
@click.option('--config', '-c', default='config/models.yaml',
              help='Path to configuration file')
def validate(config):
    """Validate configuration files."""
    try:
        cfg = Config.load_config(config)
        errors = cfg.validate()
        
        if errors:
            click.echo("Configuration errors:")
            for error in errors:
                click.echo(f"  - {error}")
        else:
            click.echo("✓ Configuration is valid")
            
    except Exception as e:
        click.echo(f"Error loading configuration: {e}")


@cli.command()
@click.option('--models', is_flag=True, help='Clean downloaded local models')
def clean(models):
    """Clean up cached files and models."""
    if models:
        models_dir = Path("models")
        if models_dir.exists():
            for file in models_dir.glob("*.gguf"):
                file.unlink()
                click.echo(f"Removed {file}")
            click.echo("Local models cleaned")
        else:
            click.echo("No models directory found")


def _get_api_keys():
    """Get API keys from environment."""
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'QWEN_API_KEY': os.getenv('QWEN_API_KEY'),
        'AI21_API_KEY': os.getenv('AI21_API_KEY')
    }


def _check_required_api_keys(models, api_keys):
    """Check if required API keys are present."""
    missing = []
    provider_key_map = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'gemini': 'GOOGLE_API_KEY',
        'qwen': 'QWEN_API_KEY',
        'ai21': 'AI21_API_KEY'
    }
    
    for model in models:
        if model.type == 'api':
            required_key = provider_key_map.get(model.provider)
            if required_key and not api_keys.get(required_key):
                missing.append(required_key)
                
    return list(set(missing))



async def _run_evaluation(cfg, api_keys, resume):
    """Run the main evaluation loop."""
    tracker = ProgressTracker()
    config_hash = cfg.get_version_hash()
    
    # Calculate total tasks
    sequences = list(cfg.prompts.keys())
    prompts_per_sequence = {seq: len(prompts) for seq, prompts in cfg.prompts.items()}
    
    for model in cfg.models:
        if model.type != 'api':  # Skip local models for now
            click.echo(f"Skipping {model.name} - local models not yet implemented")
            continue
            
        click.echo(f"\nProcessing {model.name}...")
        
        # Check if already complete
        if tracker.is_complete(model.name, config_hash, sequences, 
                             cfg.global_settings.num_runs, prompts_per_sequence):
            click.echo(f"✓ {model.name} already complete")
            continue
            
        # Create evaluator
        evaluator = EvaluatorFactory.create_evaluator(model.name, model.__dict__, api_keys)
        
        # Setup evaluator
        if not await evaluator.setup():
            click.echo(f"✗ Failed to setup {model.name}")
            continue
            
        try:
            await _process_model(evaluator, cfg, tracker, config_hash, 
                               sequences, prompts_per_sequence)
        finally:
            await evaluator.cleanup()
            
    click.echo("\n✓ Evaluation complete!")


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
                        prompt=prompt_data["text"],
                        temperature=cfg.global_settings.temperature,
                        max_tokens=cfg.global_settings.max_tokens,
                        max_retries=cfg.evaluation.max_retries
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


@cli.group()
def config():
    """Configuration management commands."""
    pass

@config.command()
@click.option('--config-dir', default='config', help='Configuration directory path')
def migrate(config_dir):
    """Migrate configuration files to MongoDB."""
    import asyncio
    from .database.connection import init_database
    from .database.migrations.config_migration import ConfigMigrationService
    
    async def run_migration():
        try:
            # Initialize database
            db = await init_database()
            
            # Run migration
            migration_service = ConfigMigrationService(db, config_dir)
            stats = await migration_service.migrate_all_configs()
            
            # Print results
            click.echo("Configuration Migration Results:")
            click.echo("=" * 40)
            
            for config_type, result in stats.items():
                if result["migrated"]:
                    click.echo(f"✅ {config_type}: Successfully migrated (hash: {result.get('config_hash', 'N/A')})")
                else:
                    error_msg = result.get("error", "Unknown error")
                    click.echo(f"❌ {config_type}: Failed - {error_msg}")
                    
        except Exception as e:
            click.echo(f"Migration failed: {e}")
            
    asyncio.run(run_migration())

@config.command()
def status():
    """Show current configuration status."""
    import asyncio
    from .database.connection import init_database
    from .database.services.config_service import ConfigService
    
    async def show_status():
        try:
            # Initialize database
            db = await init_database()
            config_service = ConfigService(db)
            
            # Get active configurations
            models_config = await config_service.get_active_models()
            prompts_config = await config_service.get_active_prompts()
            criteria_config = await config_service.get_active_criteria()
            
            click.echo("Current Configuration Status:")
            click.echo("=" * 40)
            
            if models_config:
                click.echo(f"✅ Models: Active (hash: {models_config.config_hash}, {len(models_config.models)} models)")
            else:
                click.echo("❌ Models: No active configuration")
                
            if prompts_config:
                seq_count = len(prompts_config.sequences)
                click.echo(f"✅ Prompts: Active (hash: {prompts_config.config_hash}, {seq_count} sequences)")
            else:
                click.echo("❌ Prompts: No active configuration")
                
            if criteria_config:
                criteria_count = len(criteria_config.criteria)
                click.echo(f"✅ Criteria: Active (hash: {criteria_config.config_hash}, {criteria_count} criteria)")
            else:
                click.echo("❌ Criteria: No active configuration")
                
        except Exception as e:
            click.echo(f"Status check failed: {e}")
            
    asyncio.run(show_status())


@cli.command()
@click.option('--output-dir', '-o', default='output', 
              help='Directory containing JSON files to import')
@click.option('--backup/--no-backup', default=True, 
              help='Create backup of original files before cleanup')
@click.option('--validate', is_flag=True, 
              help='Run data validation after import')
@click.option('--cleanup', is_flag=True, 
              help='Clean up original files after successful import')
def migrate(output_dir, backup, validate, cleanup):
    """Import existing JSON evaluation data into MongoDB (Phase 4)."""
    
    async def run_migration():
        from dotenv import load_dotenv
        load_dotenv()  # Load environment variables
        
        from .database.migrations.import_existing import ExistingDataImporter
        
        try:
            # Connect to database
            from .database.connection import init_database
            database = await init_database()
            importer = ExistingDataImporter(database)
            
            click.echo("=" * 50)
            click.echo("📊 StorybenchLLM Phase 4: Data Migration")
            click.echo("=" * 50)
            
            # Import data
            click.echo(f"🔄 Importing data from {output_dir}...")
            stats = await importer.import_from_output_directory(output_dir)
            
            click.echo("\n📈 Import Results:")
            click.echo(f"  • Files processed: {stats['files_processed']}")
            click.echo(f"  • Evaluations imported: {stats['evaluations_imported']}")
            click.echo(f"  • Responses imported: {stats['responses_imported']}")
            if stats['errors'] > 0:
                click.echo(f"  • Errors: {stats['errors']}")
            
            # Validate if requested
            if validate:
                click.echo("\n🔍 Validating imported data...")
                validation = await importer.validate_import_integrity()
                
                if validation['is_valid']:
                    click.echo("✅ Data validation passed!")
                else:
                    click.echo("⚠️  Data validation found issues:")
                    for issue in validation['missing_required_fields']:
                        click.echo(f"    • {issue}")
                    for anomaly in validation['timestamp_anomalies']:
                        click.echo(f"    • {anomaly}")
                    if validation['orphaned_responses'] > 0:
                        click.echo(f"    • {validation['orphaned_responses']} orphaned responses")
            
            # Cleanup if requested and successful
            if cleanup and stats['errors'] == 0:
                click.echo("\n🧹 Cleaning up original files...")
                cleanup_result = await importer.cleanup_file_dependencies(output_dir, backup)
                
                if cleanup_result['cleanup_successful']:
                    click.echo(f"✅ Moved {cleanup_result['files_moved']} files to backup")
                    if cleanup_result['backup_created']:
                        click.echo(f"📁 Backup location: {cleanup_result['backup_path']}")
                else:
                    click.echo("❌ Cleanup failed")
            
            if stats['errors'] == 0:
                click.echo("\n🎉 Phase 4 Migration Complete!")
                click.echo("✨ StorybenchLLM now uses MongoDB for all data storage")
            else:
                click.echo(f"\n⚠️  Migration completed with {stats['errors']} errors")
                
        except Exception as e:
            click.echo(f"❌ Migration failed: {e}")
            raise
            
    asyncio.run(run_migration())


@cli.command()
@click.option('--export-dir', '-e', default='export', 
              help='Directory to export data for analysis')
@click.option('--evaluation-ids', '-i', multiple=True,
              help='Specific evaluation IDs to export (optional)')
def export(export_dir, evaluation_ids):
    """Export evaluation data from MongoDB to JSON format for analysis."""
    
    async def run_export():
        from dotenv import load_dotenv
        load_dotenv()  # Load environment variables
        
        from .database.connection import init_database
        from .database.migrations.import_existing import ExistingDataImporter
        
        try:
            database = await init_database()
            importer = ExistingDataImporter(database)
            
            click.echo("📤 Exporting evaluation data...")
            
            # Convert evaluation_ids to ObjectIds if provided
            eval_ids = None
            if evaluation_ids:
                from bson import ObjectId
                eval_ids = [ObjectId(eid) for eid in evaluation_ids]
            
            export_path = await importer.export_for_analysis(export_dir, eval_ids)
            
            click.echo(f"✅ Data exported to: {export_path}")
            
        except Exception as e:
            click.echo(f"❌ Export failed: {e}")
            raise
            
    asyncio.run(run_export())


if __name__ == '__main__':
    cli()
