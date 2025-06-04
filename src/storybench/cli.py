"""Main CLI interface for storybench."""

import asyncio
import click
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from .models.config import Config
from .models.progress import ProgressTracker
from .evaluators.factory import EvaluatorFactory
from .database.services.evaluation_runner import DatabaseEvaluationRunner
from .database.services.sequence_evaluation_service import SequenceEvaluationService
from .database.repositories.criteria_repo import CriteriaRepository
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
            
            # Always fetch fresh prompts directly from Directus CMS
            click.echo("🔄 Fetching fresh prompts directly from Directus CMS...")
            from .clients.directus_client import DirectusClient, DirectusClientError
            
            try:
                directus_client = DirectusClient()
                fresh_prompts = await directus_client.fetch_prompts()
                
                if fresh_prompts and fresh_prompts.sequences:
                    # Convert to the format expected by the evaluation system
                    sequences_dict = {name: [{"name": prompt.name, "text": prompt.text} for prompt in prompt_list] 
                                    for name, prompt_list in fresh_prompts.sequences.items()}
                    
                    # Create a mock prompts_config object with the sequences
                    class MockPromptsConfig:
                        def __init__(self, sequences):
                            self.sequences = {name: [type('PromptConfig', (), prompt) for prompt in prompt_list] 
                                            for name, prompt_list in sequences.items()}
                    
                    prompts_config = MockPromptsConfig(sequences_dict)
                    click.echo(f"✅ Successfully fetched {len(sequences_dict)} prompt sequences from Directus (version {fresh_prompts.version})")
                    click.echo(f"📋 Available sequences: {list(sequences_dict.keys())}")
                else:
                    click.echo("❌ No published prompts found in Directus CMS")
                    return
                    
            except DirectusClientError as directus_error:
                click.echo(f"❌ Failed to fetch prompts from Directus: {directus_error}")
                return
            except Exception as fetch_error:
                click.echo(f"❌ Unexpected error fetching prompts from Directus: {fetch_error}")
                return
            
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


@cli.command()
@click.option('--config', '-c', default='config/models.yaml', 
              help='Path to configuration file')
@click.option('--auto-evaluate', is_flag=True, help='Automatically run LLM evaluation after response generation')
@click.option('--models', help='Comma-separated list of model names to run (default: all)')
@click.option('--sequences', help='Comma-separated list of sequence names to run (default: all)')
def run_full_pipeline(config, auto_evaluate, models, sequences):
    """Run the complete end-to-end evaluation pipeline with database storage."""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        click.echo("❌ MONGODB_URI environment variable is required")
        return
    
    if auto_evaluate and not os.getenv("OPENAI_API_KEY"):
        click.echo("❌ OPENAI_API_KEY environment variable is required for auto-evaluation")
        return
    
    try:
        asyncio.run(_run_full_pipeline(config, auto_evaluate, models, sequences))
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def _run_full_pipeline(config_path, auto_evaluate, models_filter, sequences_filter):
    """Run the complete pipeline: generate responses -> evaluate -> store results."""
    
    # Connect to database
    mongodb_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    try:
        click.echo("🔗 Connected to database")
        
        # Initialize services
        evaluation_runner = DatabaseEvaluationRunner(database)
        
        # Parse filters
        models_list = [m.strip() for m in models_filter.split(',')] if models_filter else None
        sequences_list = [s.strip() for s in sequences_filter.split(',')] if sequences_filter else None
        
        click.echo(f"🚀 Starting full pipeline...")
        if models_list:
            click.echo(f"   Models: {', '.join(models_list)}")
        if sequences_list:
            click.echo(f"   Sequences: {', '.join(sequences_list)}")
        
        # Step 1: Generate responses
        click.echo(f"\n📝 Step 1: Generating responses...")
        
        response_results = await evaluation_runner.run_evaluation(
            models_filter=models_list,
            sequences_filter=sequences_list,
            auto_evaluate=False  # We'll do evaluation separately
        )
        
        click.echo(f"✅ Response generation complete!")
        click.echo(f"   Total responses: {response_results['total_responses']}")
        click.echo(f"   New responses: {response_results['new_responses']}")
        click.echo(f"   Errors: {len(response_results.get('errors', []))}")
        
        if response_results.get('errors'):
            click.echo(f"⚠️  Errors encountered:")
            for error in response_results['errors'][:5]:  # Show first 5 errors
                click.echo(f"     {error}")
        
        # Step 2: Run evaluation if requested
        if auto_evaluate:
            click.echo(f"\n🧠 Step 2: Running LLM evaluations...")
            
            # Initialize evaluation service
            openai_api_key = os.getenv("OPENAI_API_KEY")
            sequence_eval_service = SequenceEvaluationService(database, openai_api_key)
            
            # Check if we have active criteria
            criteria_repo = CriteriaRepository(database)
            active_criteria = await criteria_repo.find_active()
            
            if not active_criteria:
                click.echo("❌ No active evaluation criteria found!")
                click.echo("   Please run the criteria setup first")
                return
            
            click.echo(f"✅ Using criteria version {active_criteria.version}")
            
            # Run sequence-aware evaluations
            eval_results = await sequence_eval_service.evaluate_all_sequences()
            
            click.echo(f"✅ Evaluation complete!")
            click.echo(f"   Sequences evaluated: {eval_results['sequences_evaluated']}")
            click.echo(f"   Total evaluations: {eval_results['total_evaluations_created']}")
            click.echo(f"   Errors: {len(eval_results.get('errors', []))}")
            
            # Generate summary
            click.echo(f"\n📊 Generating evaluation summary...")
            summary = await sequence_eval_service.get_evaluation_summary()
            
            # Save results to file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = f"pipeline_results_{timestamp}.json"
            
            output_data = {
                "pipeline_timestamp": datetime.utcnow().isoformat(),
                "config_used": config_path,
                "filters": {
                    "models": models_list,
                    "sequences": sequences_list
                },
                "response_generation": response_results,
                "evaluation_results": eval_results,
                "evaluation_summary": summary,
                "criteria_version": active_criteria.version
            }
            
            with open(results_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            click.echo(f"\n🏆 Pipeline Summary:")
            click.echo(f"   Total responses: {response_results['total_responses']}")
            click.echo(f"   Total evaluations: {summary['total_evaluations']}")
            click.echo(f"   Evaluation coverage: {summary['evaluation_coverage']:.1%}")
            
            # Show top model performance
            if summary.get('model_sequence_statistics'):
                click.echo(f"\n📈 Model Performance Preview:")
                for model_seq, stats in list(summary['model_sequence_statistics'].items())[:3]:
                    model_name = stats['model_name']
                    sequence_name = stats['sequence_name']
                    
                    # Calculate average score across all criteria
                    total_score = 0
                    total_count = 0
                    for criterion_data in stats['criteria_scores'].values():
                        total_score += criterion_data['average'] * criterion_data['count']
                        total_count += criterion_data['count']
                    
                    avg_score = total_score / total_count if total_count > 0 else 0
                    click.echo(f"   {model_name} - {sequence_name}: {avg_score:.2f}/5.0")
            
            click.echo(f"\n💾 Detailed results saved to: {results_file}")
        
        else:
            click.echo(f"\n⏭️  Skipping evaluation (use --auto-evaluate to include)")
            click.echo(f"   You can run evaluations later with the sequence evaluation service")
        
        click.echo(f"\n✅ Pipeline complete!")
        
    finally:
        client.close()
        click.echo(f"🔌 Database connection closed")


@cli.command(name='sync-prompts')
@click.option('--version', '-v', type=int, help='Specific version to sync (default: latest published)')
@click.option('--list-versions', is_flag=True, help='List all available published versions')
@click.option('--test-connection', is_flag=True, help='Test connection to Directus CMS')
def sync_prompts_command(version, list_versions, test_connection):
    """Sync prompts from Directus CMS to MongoDB."""
    asyncio.run(_sync_prompts_async(version, list_versions, test_connection))


async def _sync_prompts_async(version, list_versions, test_connection):
    """Async implementation of sync_prompts command."""
    load_dotenv()
    
    from .database.connection import init_database
    from .database.services.directus_integration_service import DirectusIntegrationService
    from .clients.directus_client import DirectusClient, DirectusClientError
    
    try:
        # Initialize database connection
        database = await init_database()
        directus_client = DirectusClient()
        integration_service = DirectusIntegrationService(database, directus_client)
        
        if test_connection:
            click.echo("Testing connection to Directus CMS...")
            is_connected = await integration_service.test_directus_connection()
            if is_connected:
                click.echo("✅ Connection successful!")
            else:
                click.echo("❌ Connection failed!")
                return
        
        if list_versions:
            click.echo("Fetching available versions from Directus...")
            versions = await integration_service.list_available_versions()
            
            if not versions:
                click.echo("No published versions found.")
                return
            
            click.echo(f"\nFound {len(versions)} published versions:")
            for v in versions:
                click.echo(f"  Version {v['version_number']}: {v['name']}")
                if v['description']:
                    click.echo(f"    Description: {v['description']}")
                click.echo(f"    Created: {v['date_created']}")
                if v['date_updated']:
                    click.echo(f"    Updated: {v['date_updated']}")
                click.echo()
            return
        
        # Sync prompts
        click.echo(f"Syncing prompts from Directus CMS...")
        if version:
            click.echo(f"Requesting version {version}")
        else:
            click.echo("Requesting latest published version")
        
        prompts = await integration_service.sync_prompts_from_directus(version)
        
        if prompts:
            click.echo("✅ Prompts synced successfully!")
            click.echo(f"Version: {prompts.version}")
            click.echo(f"Sequences: {len(prompts.sequences)}")
            
            for seq_name, seq_prompts in prompts.sequences.items():
                click.echo(f"  - {seq_name}: {len(seq_prompts)} prompts")
            
            # Show current active prompts
            active_prompts = await integration_service.get_active_prompts()
            if active_prompts:
                click.echo(f"\nActive prompts version: {active_prompts.version}")
        else:
            click.echo("❌ No prompts found to sync")
            
    except DirectusClientError as e:
        click.echo(f"❌ Directus error: {e}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command('parallel')
@click.option('--config', '-c', default='config/models.yaml', help='Path to models config')
@click.option('--prompts', '-p', default='config/prompts.json', help='Path to prompts config')
@click.option('--models', '-m', help='Comma-separated list of specific models to run')
@click.option('--sequences', '-s', help='Comma-separated list of specific sequences to run')
@click.option('--runs', '-r', default=3, help='Number of runs per sequence (default: 3)')
@click.option('--max-concurrent', default=5, help='Max concurrent sequences (default: 5)')
@click.option('--dry-run', is_flag=True, help='Validate config without running')
def parallel_evaluation(config, prompts, models, sequences, runs, max_concurrent, dry_run):
    """
    Run parallel evaluation with 5x speedup via sequence-level parallelization.
    
    Phase 2.0 feature: Runs 5 sequences concurrently per model for dramatic
    performance improvement while maintaining context isolation.
    """
    click.echo("🚀 StoryBench Phase 2.0 - Parallel Evaluation")
    click.echo("=" * 60)
    
    async def run_parallel():
        try:
            # Load configuration
            import yaml
            with open(config, 'r') as f:
                config_data = yaml.safe_load(f)
            
            with open(prompts, 'r') as f:
                prompts_data = json.load(f)
            
            # Filter models if specified
            all_models = []
            for provider, provider_models in config_data['models'].items():
                for model in provider_models:
                    if model.get('enabled', True):
                        model['provider'] = provider
                        all_models.append(model)
            
            if models:
                model_names = [m.strip() for m in models.split(',')]
                all_models = [m for m in all_models if m['name'] in model_names]
            
            # Filter sequences if specified
            if sequences:
                sequence_names = [s.strip() for s in sequences.split(',')]
                prompts_data = {k: v for k, v in prompts_data.items() if k in sequence_names}
            
            click.echo(f"Configuration loaded:")
            click.echo(f"  📊 Models: {len(all_models)}")
            click.echo(f"  📝 Sequences: {len(prompts_data)}")
            click.echo(f"  🔄 Runs per sequence: {runs}")
            click.echo(f"  ⚡ Max concurrent sequences: {max_concurrent}")
            click.echo(f"  📈 Total API calls: {len(all_models) * len(prompts_data) * 3 * runs}")
            
            if dry_run:
                click.echo("\n✅ Dry run successful - configuration valid")
                return
            
            # Check API keys
            api_keys = _get_api_keys()
            missing_keys = []
            for model in all_models:
                provider = model['provider']
                if provider == 'openai' and not api_keys['OPENAI_API_KEY']:
                    missing_keys.append('OPENAI_API_KEY')
                elif provider == 'anthropic' and not api_keys['ANTHROPIC_API_KEY']:
                    missing_keys.append('ANTHROPIC_API_KEY')
                elif provider == 'google' and not api_keys['GOOGLE_API_KEY']:
                    missing_keys.append('GOOGLE_API_KEY')
                # Add other providers as needed
            
            if missing_keys:
                click.echo(f"❌ Missing API keys: {', '.join(set(missing_keys))}")
                return
            
            # Initialize database
            click.echo("\n🔌 Connecting to database...")
            from .database.connection import init_database
            database = await init_database()
            click.echo("✅ Database connected")
            
            # Initialize parallel evaluation runner
            click.echo("⚡ Initializing parallel evaluation runner...")
            runner = DatabaseEvaluationRunner(database, enable_parallel=True)
            runner.parallel_runner.max_concurrent_sequences = max_concurrent
            click.echo("✅ Parallel runner ready")
            
            # Start evaluation
            click.echo("\n🚀 Starting parallel evaluation...")
            evaluation = await runner.start_evaluation(
                models=[m['name'] for m in all_models],
                sequences=prompts_data,
                criteria={"parallel_test": True},
                global_settings={"num_runs": runs}
            )
            
            evaluation_id = str(evaluation.id)
            click.echo(f"📋 Evaluation ID: {evaluation_id}")
            
            # Create evaluator factory
            def create_evaluator(model_config):
                from .evaluators.api_evaluator import APIEvaluator
                provider = model_config['provider']
                
                if provider == 'openai':
                    return APIEvaluator(model_config['model_id'], api_keys['OPENAI_API_KEY'], 'openai')
                elif provider == 'anthropic':
                    return APIEvaluator(model_config['model_id'], api_keys['ANTHROPIC_API_KEY'], 'anthropic')
                elif provider == 'google':
                    return APIEvaluator(model_config['model_id'], api_keys['GOOGLE_API_KEY'], 'google')
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
            
            # Run parallel evaluation
            start_time = datetime.now()
            results = await runner.run_parallel_evaluation(
                evaluation_id=evaluation_id,
                models=all_models,
                sequences=prompts_data,
                num_runs=runs,
                evaluator_factory=create_evaluator
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Results summary
            click.echo("\n" + "=" * 60)
            click.echo("🎉 PARALLEL EVALUATION COMPLETE")
            click.echo("=" * 60)
            
            if results.get('success', False):
                click.echo(f"✅ Evaluation completed successfully!")
                click.echo(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
                click.echo(f"👥 Workers: {results['successful_workers']}/{results['total_workers']} successful")
                
                if 'performance_metrics' in results:
                    metrics = results['performance_metrics']
                    click.echo(f"📊 Throughput: {metrics.get('average_throughput_per_minute', 0):.1f} prompts/min")
                    if metrics.get('parallelization_speedup', 0) > 0:
                        click.echo(f"🚀 Speedup: {metrics['parallelization_speedup']:.1f}x vs sequential")
                
                click.echo(f"\n💾 Results saved to evaluation ID: {evaluation_id}")
            else:
                click.echo(f"❌ Evaluation failed: {results.get('error', 'Unknown error')}")
            
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_parallel())


if __name__ == '__main__':
    cli()

