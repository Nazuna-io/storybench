#!/usr/bin/env python3
"""
End-to-end CLI for StorybenchLLM: Generate responses and evaluate them.
This script runs the complete pipeline from model API calls to evaluation storage.
"""

import asyncio
import os
import json
import click
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Import the services we need
import sys
sys.path.append('src')

from storybench.database.services.sequence_evaluation_service import SequenceEvaluationService
from storybench.database.repositories.criteria_repo import CriteriaRepository
from storybench.database.repositories.response_repo import ResponseRepository
from storybench.evaluators.factory import EvaluatorFactory
from storybench.models.config import Config


@click.command()
@click.option('--models', help='Comma-separated list of model names to run (default: all)')
@click.option('--sequences', help='Comma-separated list of sequence names to run (default: all)')
@click.option('--auto-evaluate', is_flag=True, help='Automatically run LLM evaluation after response generation')
@click.option('--config', '-c', default='config/models.yaml', help='Path to configuration file')
def main(models, sequences, auto_evaluate, config):
    """Run the complete end-to-end evaluation pipeline."""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        click.echo("❌ MONGODB_URI environment variable is required")
        return
    
    try:
        asyncio.run(_run_pipeline(models, sequences, auto_evaluate, config))
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def _run_pipeline(models_filter, sequences_filter, auto_evaluate, config_path):
    """Run the complete pipeline."""
    
    # Connect to database
    mongodb_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    try:
        click.echo("🔗 Connected to database")
        
        # Load configuration
        click.echo(f"📋 Loading configuration from {config_path}")
        cfg = Config.load_config(config_path)
        
        # Validate configuration
        errors = cfg.validate()
        if errors:
            click.echo("❌ Configuration errors:")
            for error in errors:
                click.echo(f"   {error}")
            return
        
        click.echo(f"✅ Configuration valid - {len(cfg.models)} models, {len(cfg.prompts)} prompt sequences")
        
        # Parse filters
        models_list = [m.strip() for m in models_filter.split(',')] if models_filter else None
        sequences_list = [s.strip() for s in sequences_filter.split(',')] if sequences_filter else None
        
        # Filter models and sequences
        if models_list:
            cfg.models = [m for m in cfg.models if m.name in models_list]
            click.echo(f"🎯 Filtered to models: {[m.name for m in cfg.models]}")
        
        if sequences_list:
            cfg.prompts = {k: v for k, v in cfg.prompts.items() if k in sequences_list}
            click.echo(f"🎯 Filtered to sequences: {list(cfg.prompts.keys())}")
        
        if not cfg.models:
            click.echo("❌ No models to evaluate after filtering")
            return
            
        if not cfg.prompts:
            click.echo("❌ No prompt sequences to evaluate after filtering")
            return
        
        api_keys = _get_api_keys()
        missing_keys = _check_required_api_keys(cfg.models, api_keys)
        if missing_keys:
            click.echo("❌ Missing required API keys:")
            for key in missing_keys:
                click.echo(f"   {key}")
            return
        
        # Initialize repositories
        response_repo = ResponseRepository(database)
        
        # Step 1: Generate responses
        click.echo(f"\n📝 Step 1: Generating responses...")
        
        total_responses = 0
        new_responses = 0
        errors = []
        
        for model in cfg.models:
            if model.type != 'api':
                click.echo(f"⏭️  Skipping {model.name} - only API models supported")
                continue
                
            click.echo(f"\n🤖 Processing model: {model.name}")
            
            # Initialize evaluator for this model
            model_config = {
                "type": model.type,
                "provider": model.provider,
                "model_name": model.model_name
            }
            evaluator = EvaluatorFactory.create_evaluator(model.name, model_config, api_keys)
            
            # Setup the evaluator
            setup_success = await evaluator.setup()
            if not setup_success:
                click.echo(f"   ❌ Failed to setup evaluator for {model.name}")
                continue
            
            for sequence_name, prompts in cfg.prompts.items():
                click.echo(f"   📚 Sequence: {sequence_name}")
                
                for run in range(cfg.global_settings.num_runs):
                    click.echo(f"      🔄 Run {run + 1}/{cfg.global_settings.num_runs}")
                    
                    for prompt_idx, prompt in enumerate(prompts):
                        prompt_name = prompt.get('name', f'prompt_{prompt_idx}')
                        prompt_text = prompt['text']
                        
                        # Check if response already exists
                        existing_responses = await response_repo.find_many({
                            "model_name": model.name,
                            "sequence": sequence_name,
                            "run": run,
                            "prompt_index": prompt_idx
                        }, limit=1)
                        
                        if existing_responses:
                            click.echo(f"         ⏭️  {prompt_name} (already exists)")
                            total_responses += 1
                            continue
                        
                        try:
                            # Generate response
                            click.echo(f"         🎯 {prompt_name}...")
                            
                            start_time = datetime.now(timezone.utc)
                            response_result = await evaluator.generate_response(prompt_text)
                            end_time = datetime.now(timezone.utc)
                            generation_time = (end_time - start_time).total_seconds()
                            
                            # Extract response text from the result dict
                            response_text = response_result.get("response", "")
                            
                            # Save to database
                            from storybench.database.models import Response, ResponseStatus
                            response = Response(
                                evaluation_id="end_to_end_run",  # Use a default evaluation ID for standalone runs
                                model_name=model.name,
                                sequence=sequence_name,
                                run=run,
                                prompt_index=prompt_idx,
                                prompt_name=prompt_name,
                                prompt_text=prompt_text,
                                response=response_text,
                                generation_time=generation_time,
                                status=ResponseStatus.COMPLETED
                            )
                            
                            await response_repo.create(response)
                            
                            total_responses += 1
                            new_responses += 1
                            click.echo(f"         ✅ Generated ({generation_time:.1f}s)")
                            
                            # Small delay to be nice to APIs
                            await asyncio.sleep(1)
                            
                        except Exception as e:
                            error_msg = f"Error generating {model.name}/{sequence_name}/run{run}/{prompt_name}: {str(e)}"
                            errors.append(error_msg)
                            click.echo(f"         ❌ {str(e)}")
        
        click.echo(f"\n✅ Response generation complete!")
        click.echo(f"   Total responses: {total_responses}")
        click.echo(f"   New responses: {new_responses}")
        click.echo(f"   Errors: {len(errors)}")
        
        if errors:
            click.echo(f"\n⚠️  Errors encountered:")
            for error in errors[:5]:  # Show first 5 errors
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
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            results_file = f"pipeline_results_{timestamp}.json"
            
            output_data = {
                "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
                "config_used": config_path,
                "filters": {
                    "models": models_filter,
                    "sequences": sequences_filter
                },
                "response_generation": {
                    "total_responses": total_responses,
                    "new_responses": new_responses,
                    "errors": errors
                },
                "evaluation_results": eval_results,
                "evaluation_summary": summary,
                "criteria_version": active_criteria.version
            }
            
            with open(results_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            click.echo(f"\n🏆 Pipeline Summary:")
            click.echo(f"   Total responses: {total_responses}")
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
            click.echo(f"   You can run evaluations later with: python3 run_fresh_sequence_evaluations.py")
        
        click.echo(f"\n✅ Pipeline complete!")
        
    finally:
        client.close()
        click.echo(f"🔌 Database connection closed")


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


if __name__ == "__main__":
    main()
