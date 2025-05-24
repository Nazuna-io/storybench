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


if __name__ == '__main__':
    cli()
