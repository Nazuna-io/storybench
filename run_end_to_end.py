#!/usr/bin/env python3
"""
End-to-end CLI for StorybenchLLM: Generate responses and evaluate them.
This script runs the complete pipeline from model API calls to evaluation storage.
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import click
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Import the services we need
import sys
sys.path.append('src')

from storybench.database.services.sequence_evaluation_service import SequenceEvaluationService
from storybench.database.services.config_service import ConfigService
from storybench.database.repositories.criteria_repo import CriteriaRepository
from storybench.database.repositories.response_repo import ResponseRepository
from storybench.evaluators.factory import EvaluatorFactory
from storybench.database.models import Response
from storybench.models.config import Config, ModelConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.command()
@click.option('--models', help='Comma-separated list of model names to run (default: all)')
@click.option('--sequences', help='Comma-separated list of sequence names to run (default: all)')
@click.option('--auto-evaluate', is_flag=True, help='Automatically run LLM evaluation after response generation')
@click.option('--config', '-c', default='config/models.yaml', help='Path to API models configuration file (models.yaml)')
@click.option('--local-config', default=None, help='Path to local models JSON configuration file (e.g., local_models.json)')
@click.option('--evaluator-model', default=None, help='Name of the model to use for evaluation (e.g., "gpt-4-turbo-preview" or a local model name). If not specified, defaults to OpenAI gpt-4-turbo-preview. Ensure the model is defined in API or local configs.')
def main(models, sequences, auto_evaluate, config, local_config, evaluator_model):
    """Run the complete end-to-end evaluation pipeline."""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        click.echo("❌ MONGODB_URI environment variable is required")
        return
    
    try:
        asyncio.run(_run_pipeline(models, sequences, auto_evaluate, config, local_config, evaluator_model))
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def _run_pipeline(models_filter, sequences_filter, auto_evaluate, config_path, local_config_path, evaluator_model_name):
    """Run the complete pipeline."""
    
    database_client = None  # Initialize to None for finally block
    try:
        # Connect to database
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            click.echo("❌ MONGODB_URI environment variable is required")
            return
            
        database_client = AsyncIOMotorClient(mongodb_uri)
        database = database_client["storybench"]
        logger.info("🔗 Connected to database")
        
        mongo_uri_from_env = os.getenv("MONGODB_URI")
        db_name_from_env = os.getenv("MONGODB_DATABASE_NAME", "storybench_db")
        logger.info(f"run_end_to_end.py is configured to use MongoDB URI from env: {mongo_uri_from_env}")
        logger.info(f"run_end_to_end.py is configured to use Database Name from env: {db_name_from_env}")
        if database_client:
            # For SRV, address might be None initially or represent the seed list, nodes is more reliable for connected nodes.
            logger.info(f"Actual client 'address' (may be seed or None for SRV): {database_client.address}")
            logger.info(f"Actual client connected 'nodes': {database_client.nodes}")
        
        # Load API model configuration
        click.echo(f"📋 Loading API model configuration from {config_path}")
        cfg = Config.load_config(config_path)
        
        # Load prompts from database (override JSON file prompts)
        try:
            config_service = ConfigService(database)
            prompts_config = await config_service.get_active_prompts()
            if prompts_config and hasattr(prompts_config, 'sequences') and isinstance(prompts_config.sequences, dict):
                cfg.prompts = prompts_config.sequences
                click.echo(f"✅ Loaded prompts from database: {len(cfg.prompts)} sequences")
            else:
                click.echo("⚠️ No prompts found in database, using prompts from JSON file")
        except Exception as e:
            click.echo(f"⚠️ Error loading prompts from database: {str(e)}, using prompts from JSON file")
        
        # Validate API model configuration
        errors = cfg.validate()
        if errors:
            click.echo("❌ API model configuration errors:")
            for error in errors:
                click.echo(f"   {error}")
            return
        click.echo(f"✅ API model configuration valid - {len(cfg.models)} models, {len(cfg.prompts)} prompt sequences")

        # Load local models configuration if path is provided
        parsed_local_models = []
        if local_config_path:
            click.echo(f"📋 Loading local models configuration from {local_config_path}")
            try:
                with open(local_config_path, 'r') as f:
                    local_models_data = json.load(f)
                
                for lm_entry in local_models_data.get("models", []):
                    model_config_args = {
                        "name": lm_entry.get("name"),
                        "type": "local",
                        "provider": lm_entry.get("provider", "local_default_provider"),
                        "model_name": lm_entry.get("model_filename", lm_entry.get("name")), 
                        "repo_id": lm_entry.get("model_repo_id"),
                        "filename": lm_entry.get("model_filename"),
                        "subdirectory": lm_entry.get("subdirectory"),
                        "model_settings": lm_entry.get("model_settings", lm_entry.get("settings")) # Try both keys for backwards compatibility
                    }
                    final_mc_args = {k: v for k, v in model_config_args.items() if v is not None}
                    parsed_local_models.append(ModelConfig(**final_mc_args))
                
                cfg.models.extend(parsed_local_models) # Add local models to the main list
                click.echo(f"✅ Loaded {len(parsed_local_models)} local models.")
            except FileNotFoundError:
                click.echo(f"⚠️ Local models configuration file not found: {local_config_path}")
            except json.JSONDecodeError:
                click.echo(f"❌ Error decoding JSON from local models file: {local_config_path}")
            except Exception as e:
                click.echo(f"❌ Error loading local models configuration: {e}")
                return # Stop if local model loading fails critically
        
        click.echo(f"ℹ️ Total models available: {len(cfg.models)}")
        
        # Store a full list of all configured models BEFORE filtering for response generation
        all_loaded_model_configs = list(cfg.models) 

        # Parse filters for models and sequences
        models_list_filter = [m.strip() for m in models_filter.split(',')] if models_filter else None
        sequences_list_filter = [s.strip() for s in sequences_filter.split(',')] if sequences_filter else None
        
        # Filter models for response generation
        if models_list_filter:
            cfg.models = [m for m in cfg.models if m.name in models_list_filter]
            click.echo(f"🎯 Filtered to models for response generation: {[m.name for m in cfg.models]}")
        
        # Filter sequences for response generation
        if sequences_list_filter:
            cfg.prompts = {k: v for k, v in cfg.prompts.items() if k in sequences_list_filter}
            click.echo(f"🎯 Filtered to sequences for response generation: {list(cfg.prompts.keys())}")
        
        if not cfg.models:
            click.echo("❌ No models to process after filtering.")
            return
        if not cfg.prompts:
            click.echo("❌ No prompt sequences to process after filtering.")
            return
            
        api_keys = _get_api_keys()
        # Check API keys only for the API models selected for response generation
        api_models_for_key_check = [m for m in cfg.models if m.type == 'api']
        if api_models_for_key_check:
            missing_keys = _check_required_api_keys(api_models_for_key_check, api_keys)
            if missing_keys:
                click.echo("❌ Missing required API keys for response generation:")
                for key in missing_keys:
                    click.echo(f"   {key}")
                return
        
        # Initialize repositories
        response_repo = ResponseRepository(database)
            
        # Step 1: Generate responses
        click.echo(f"\n📝 Step 1: Generating responses...")
        total_responses_generated_count = 0
        new_responses_created_count = 0
        generation_errors = []
            
        for model_config in cfg.models: # Iterate over filtered models for generation
            click.echo(f"\n🤖 Processing model: {model_config.name} (Type: {model_config.type})")
            
            current_model_api_keys = {}
            factory_config = {
                "type": model_config.type,
                "provider": model_config.provider,
                "model_name": model_config.model_name, # model_name from ModelConfig
                "repo_id": model_config.repo_id,       # repo_id from ModelConfig
                "filename": model_config.filename,     # filename from ModelConfig
                "subdirectory": model_config.subdirectory # subdirectory from ModelConfig
            }

            if model_config.type == 'local':
                if model_config.model_settings: # Merge model_settings if they exist
                    factory_config.update(model_config.model_settings)
                    click.echo(f"   Using model_settings for local model {model_config.name}: {model_config.model_settings}")
            elif model_config.type == 'api':
                current_model_api_keys = api_keys # Pass all keys, factory will pick

            try:
                # Pass the constructed factory_config dictionary to the factory
                evaluator = EvaluatorFactory.create_evaluator(
                    name=model_config.name,
                    config=factory_config, 
                    api_keys=current_model_api_keys
                )
            except Exception as e:
                click.echo(f"❌ Error creating evaluator for model {model_config.name}: {e}")
                generation_errors.append(f"Evaluator creation for {model_config.name}: {e}")
                continue

            try:
                click.echo(f"   ⚙️ Setting up evaluator for {model_config.name}...")
                await evaluator.setup() # Ensure evaluator is set up
                click.echo(f"   ✅ Evaluator for {model_config.name} ready.")
            except Exception as e:
                click.echo(f"❌ Error setting up evaluator for model {model_config.name}: {e}")
                generation_errors.append(f"Evaluator setup for {model_config.name}: {e}")
                continue

            for seq_name, prompts in cfg.prompts.items(): # Iterate over filtered sequences
                click.echo(f"   📚 Sequence: {seq_name}")
                full_sequence_text = ""
                for i in range(cfg.global_settings.num_runs):
                    click.echo(f"      🔄 Run {i+1}/{cfg.global_settings.num_runs}")
                    for prompt_idx, prompt_obj in enumerate(prompts):
                        # Handle both dictionary (JSON) and object (database) formats
                        if hasattr(prompt_obj, 'text'):
                            prompt_text = prompt_obj.text
                            prompt_name = prompt_obj.name
                        else:
                            prompt_text = prompt_obj['text']
                            prompt_name = prompt_obj['name']
                            
                        prompt_text_to_send = full_sequence_text + prompt_text
                        try:
                            response_text = await evaluator.generate_response(prompt_text_to_send, **model_config.model_settings if model_config.model_settings else {})
                            if response_text and isinstance(response_text, dict) and 'text' in response_text and response_text['text']:
                                generated_text_str = response_text['text']
                                generation_time_val = response_text.get('generation_time', 0.0) # Get generation_time
                                full_sequence_text += generated_text_str + "\n\n" # Append for context
                                response_data = {
                                    "evaluation_id": "", # Placeholder, model expects str
                                    "model_name": model_config.name,
                                    "model_provider": model_config.provider, # Not in Response model, but keep for now if needed elsewhere
                                    "sequence": seq_name, # Changed from sequence_name
                                    "run": i + 1, # Changed from run_number
                                    "prompt_index": prompt_idx, # Added
                                    "prompt_name": prompt_name,
                                    "prompt_text": prompt_text,
                                    "full_prompt_text": prompt_text_to_send, # Not in Response model
                                    "response": generated_text_str, # Changed from response_text
                                    "generation_time": generation_time_val, # Added
                                    "created_at": datetime.now(timezone.utc), # Not in Response model, completed_at is auto
                                    # status is defaulted in model
                                }
                                # Filter out keys not in Response model before creating instance
                                response_fields = Response.model_fields.keys()
                                filtered_response_data = {k: v for k, v in response_data.items() if k in response_fields}
                                logger.debug(f"Attempting to create response with data: {{key: val for key, val in filtered_response_data.items() if key != 'response'}} ... Response Text Length: {len(filtered_response_data.get('response',''))}")
                                response_instance = Response(**filtered_response_data)
                                try:
                                    created_response_doc = await response_repo.create(response_instance)
                                    if created_response_doc and created_response_doc.id:
                                        logger.info(f"Successfully created response with ID: {created_response_doc.id}, Eval ID: {created_response_doc.evaluation_id}, Model: {created_response_doc.model_name}, Seq: {created_response_doc.sequence}, Run: {created_response_doc.run}, PromptIdx: {created_response_doc.prompt_index}")
                                    else:
                                        logger.error("Failed to create response or retrieve ID after creation (created_response_doc is None or has no ID).")
                                except Exception as e_create:
                                    logger.error(f"Error during response_repo.create: {e_create}")
                                    import traceback
                                    logger.error(traceback.format_exc())
                                new_responses_created_count += 1
                            else:
                                click.echo(f"      ⚠️ Empty response for prompt: {prompt_name}")
                                generation_errors.append(f"Empty response: {model_config.name}/{seq_name}/{prompt_name}/Run{i+1}")
                        except Exception as e:
                            click.echo(f"      ❌ Error generating response for prompt {prompt_name}: {e}")
                            generation_errors.append(f"Generation error: {model_config.name}/{seq_name}/{prompt_name}/Run{i+1}: {e}")
                            # Decide if we should break inner loops or continue
                    total_responses_generated_count +=1 # Counts a "full sequence run" completion
            
            if hasattr(evaluator, 'cleanup'): # Cleanup for local models
                await evaluator.cleanup()

        _print_response_generation_summary(total_responses_generated_count, new_responses_created_count, generation_errors)

        if auto_evaluate:
            click.echo("\n📊 Step 2: Evaluating responses...")
            
            evaluator_mc_for_eval: Optional[ModelConfig] = None # Will hold the ModelConfig for the evaluator
            
            # Use the comprehensive list of all_loaded_model_configs for evaluator selection
            if evaluator_model_name:
                click.echo(f"🔎 Searching for specified evaluator model: {evaluator_model_name} in all loaded models...")
                for m_conf in all_loaded_model_configs: # Search in the comprehensive list
                    if m_conf.name == evaluator_model_name:
                        evaluator_mc_for_eval = m_conf
                        break
                if not evaluator_mc_for_eval:
                    click.echo(f"❌ Evaluator model '{evaluator_model_name}' not found in any loaded configurations. Available: {[m.name for m in all_loaded_model_configs]}")
                    return 
                click.echo(f"✅ Using specified evaluator model: {evaluator_mc_for_eval.name} (Type: {evaluator_mc_for_eval.type}, Provider: {evaluator_mc_for_eval.provider})")
            else:
                # Default evaluator model if none specified
                default_eval_model_name = "gpt-4-turbo-preview" # Example default
                default_eval_provider = "openai"
                click.echo(f"ℹ️ No --evaluator-model specified. Defaulting to {default_eval_provider}/{default_eval_model_name} for evaluation.")
                for m_conf in all_loaded_model_configs: # Search in the comprehensive list
                    if m_conf.name == default_eval_model_name and m_conf.provider == default_eval_provider:
                        evaluator_mc_for_eval = m_conf
                        click.echo(f"✅ Found default evaluator model in loaded configurations: {evaluator_mc_for_eval.name}")
                        break
                if not evaluator_mc_for_eval: 
                    click.echo(f"ℹ️ Default evaluator {default_eval_provider}/{default_eval_model_name} not in loaded configs. Creating ModelConfig on-the-fly.")
                    evaluator_mc_for_eval = ModelConfig(
                        name=default_eval_model_name, type="api", provider=default_eval_provider, model_name=default_eval_model_name
                    )
            
            eval_api_keys_for_service = {}
            if evaluator_mc_for_eval.type == 'api':
                missing_eval_keys = _check_required_api_keys([evaluator_mc_for_eval], api_keys) 
                if missing_eval_keys:
                    click.echo(f"❌ Missing API key for evaluator model {evaluator_mc_for_eval.name} (Provider: {evaluator_mc_for_eval.provider}): {', '.join(missing_eval_keys)}")
                    return 
                eval_api_keys_for_service = api_keys 
            
            # Local evaluator model settings are now part of evaluator_mc_for_eval.model_settings
            if evaluator_mc_for_eval.type == 'local' and evaluator_mc_for_eval.model_settings:
                click.echo(f"   Local evaluator model {evaluator_mc_for_eval.name} will use its model_settings: {evaluator_mc_for_eval.model_settings}")

            try:
                logger.info(f"Attempting to initialize SequenceEvaluationService with evaluator_mc_for_eval: Name='{evaluator_mc_for_eval.name}', Type='{evaluator_mc_for_eval.type}', Provider='{evaluator_mc_for_eval.provider}', ModelName='{evaluator_mc_for_eval.model_name}', Settings='{evaluator_mc_for_eval.model_settings}'")
                click.echo(f"🔧 Initializing SequenceEvaluationService with evaluator: {evaluator_mc_for_eval.name}")
                evaluation_service = SequenceEvaluationService(
                    database=database,
                    evaluator_model_config=evaluator_mc_for_eval, 
                    api_keys=eval_api_keys_for_service
                    # evaluator_specific_config argument removed
                )
                
                # Initialize the evaluator within the service (e.g., call setup() for local models)
                await evaluation_service.initialize()
                
                criteria_repo = CriteriaRepository(database)
                active_criteria = await criteria_repo.find_active()
                if not active_criteria:
                    click.echo("❌ No active evaluation criteria found! Please run criteria setup.")
                    return
                click.echo(f"✅ Using criteria version {active_criteria.version} for evaluation.")

                eval_results = await evaluation_service.evaluate_all_sequences()
                
                click.echo(f"✅ Evaluation complete using {evaluator_mc_for_eval.name}!")
                click.echo(f"   Sequences evaluated: {eval_results.get('sequences_evaluated', 0)}")
                click.echo(f"   Total evaluations created: {eval_results.get('total_evaluations_created', 0)}")
                if eval_results.get('errors'):
                    click.echo(f"   Evaluation errors: {len(eval_results['errors'])}")
                    for err_idx, err_msg in enumerate(eval_results['errors'][:3]):
                        click.echo(f"     Error {err_idx+1}: {err_msg}")

                click.echo(f"\n📊 Generating evaluation summary...")
                summary = await evaluation_service.get_evaluation_summary()
                print_evaluation_summary(summary) 

                # Save results to file
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                results_file = f"pipeline_results_{timestamp}.json"
                output_data = {
                    "timestamp": timestamp,
                    "models_filter": models_filter,
                    "sequences_filter": sequences_filter,
                    "auto_evaluate": auto_evaluate,
                    "evaluator_model_used": evaluator_mc_for_eval.name,
                    "generation_summary": {
                        "total_runs_processed": total_responses_generated_count,
                        "new_responses_created": new_responses_created_count,
                        "errors": generation_errors
                    },
                    "evaluation_results_summary": eval_results, # from evaluate_all_sequences
                    "detailed_evaluation_metrics": summary # from get_evaluation_summary
                }
                with open(results_file, 'w') as f:
                    json.dump(output_data, f, indent=4)
                click.echo(f"\n💾 Full pipeline results saved to {results_file}")

            except Exception as e:
                click.echo(f"❌ Error during evaluation step with {evaluator_mc_for_eval.name if evaluator_mc_for_eval else 'default evaluator'}: {e}")
                import traceback
                traceback.print_exc()
        else:
            click.echo("\nℹ️ Auto-evaluation skipped as per --no-auto-evaluate flag.")

    except Exception as e: # Catch-all for pipeline-level errors
        click.echo(f"❌ An unexpected error occurred in the pipeline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if database_client:
            database_client.close()
            click.echo("\n🔌 Database connection closed.")
def _print_response_generation_summary(total_runs, new_responses, errors_list):
    """Prints a summary of the response generation phase."""
    click.echo(f"\n✅ Response generation complete!")
    click.echo(f"   Total sequence runs processed: {total_runs}")
    click.echo(f"   New responses created in DB: {new_responses}")
    if errors_list:
        click.echo(f"   Generation errors encountered: {len(errors_list)}")
        for i, err in enumerate(errors_list[:5]): # Print first 5 errors
            click.echo(f"      Error {i+1}: {err}")
        if len(errors_list) > 5:
            click.echo(f"      ... and {len(errors_list) - 5} more errors.")
    else:
        click.echo(f"   No generation errors.")

def print_evaluation_summary(summary: Dict[str, Any]):
    """Prints a formatted summary of the evaluation results."""
    click.echo(f"\n🏆 Evaluation Summary:")
    click.echo(f"   Total responses in DB: {summary.get('total_responses', 0)}")
    click.echo(f"   Total evaluations in DB: {summary.get('total_evaluations', 0)}")
    click.echo(f"   Overall evaluation coverage: {summary.get('evaluation_coverage', 0.0):.1%}")

    if summary.get('model_sequence_statistics'):
        click.echo(f"\n📈 Model Performance Preview (Top 3 by overall score):")
        # Sort by average score if possible, or just take first few
        # This is a simplified preview; more complex sorting could be added
        preview_count = 0
        for model_seq_key, stats_val in summary['model_sequence_statistics'].items():
            if preview_count >= 3: 
                break
            
            model_name_stat = stats_val.get('model_name', 'N/A')
            sequence_name_stat = stats_val.get('sequence_name', 'N/A')
            criteria_scores_stat = stats_val.get('criteria_scores', {})
            
            total_weighted_score = 0
            total_criteria_observations = 0
            
            for crit_name, crit_data in criteria_scores_stat.items():
                total_weighted_score += crit_data.get('average', 0) * crit_data.get('count', 0)
                total_criteria_observations += crit_data.get('count', 0)
            
            avg_overall_score = total_weighted_score / total_criteria_observations if total_criteria_observations > 0 else 0
            click.echo(f"   - {model_name_stat} / {sequence_name_stat}: Avg Score {avg_overall_score:.2f}/5.0 ({total_criteria_observations} criteria observations)")
            preview_count += 1
    else:
        click.echo("   No detailed model/sequence statistics available in this summary.")


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
