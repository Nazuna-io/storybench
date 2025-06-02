#!/usr/bin/env python3
"""
FULL API PRODUCTION TEST: 12 Models × 15 Prompts × 3 Runs = 540 Responses + Evaluations
=======================================================================================
Production pipeline testing with complete Directus integration:
- 12 API models from test plan specification
- 15 prompts from Directus (5 sequences × 3 prompts)
- 3 runs per sequence with context resets between sequences (for coherence testing)
- Temperature 1.0 for prompts, 0.3 for evaluation
- 7 evaluation criteria from Directus
- Gemini-2.5-Pro for evaluation
- Full API connectivity and model validation
- MongoDB storage for all data
- Skip models with API problems and continue to next model
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.clients.directus_client import DirectusClient
from storybench.database.connection import DatabaseConnection
from storybench.evaluators.api_evaluator import APIEvaluator
from storybench.web.services.lightweight_api_test import LightweightAPITester


def validate_environment():
    """Validate required environment variables."""
    required_vars = {
        "DIRECTUS_URL": "Directus CMS URL",
        "DIRECTUS_TOKEN": "Directus API token", 
        "MONGODB_URI": "MongoDB connection string",
        "GOOGLE_API_KEY": "Google Gemini API key for evaluation"
    }
    
    missing = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({desc})")
    
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)
    
    print("✅ Environment variables validated")


async def load_and_validate_models() -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """Load models from test plan specification (ignoring api-models-list.txt)."""
    print(f"\n🌟 STEP: LOAD TEST PLAN MODELS")
    print("-" * 50)
    
    # TEST PLAN MODELS - Exactly 12 models as specified
    models = [
        {"provider": "anthropic", "model_name": "claude-opus-4-20250514"},
        {"provider": "anthropic", "model_name": "claude-sonnet-4-20250514"},
        {"provider": "anthropic", "model_name": "claude-3-7-sonnet-20250219"},
        {"provider": "openai", "model_name": "gpt-4.1"},
        {"provider": "openai", "model_name": "gpt-4o"},
        {"provider": "openai", "model_name": "o4-mini"},
        {"provider": "gemini", "model_name": "gemini-2.5-flash-preview-05-20"},
        {"provider": "gemini", "model_name": "gemini-2.5-pro-preview-05-06"},
        {"provider": "deepinfra", "model_name": "Qwen/Qwen3-235B-A22B"},
        {"provider": "deepinfra", "model_name": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
        {"provider": "deepinfra", "model_name": "deepseek-ai/DeepSeek-R1"},
        {"provider": "deepinfra", "model_name": "deepseek-ai/DeepSeek-R1-0528"},
        {"provider": "deepinfra", "model_name": "deepseek-ai/DeepSeek-V3-0324"}
    ]
    
    print(f"   📋 Using {len(models)} models from test plan specification")
    
    # Prepare API keys
    api_keys = {}
    api_providers = set(model["provider"] for model in models)
    
    for provider in api_providers:
        # Special case for gemini - uses GOOGLE_API_KEY
        if provider == "gemini":
            env_var = "GOOGLE_API_KEY"
        else:
            env_var = f"{provider.upper()}_API_KEY"
            
        api_key = os.getenv(env_var)
        if api_key:
            api_keys[provider] = api_key
            print(f"   ✅ {provider}: API key found")
        else:
            print(f"   ⚠️  {provider}: API key missing ({env_var})")
    
    return models, api_keys


async def test_api_connectivity(models: List[Dict[str, str]], api_keys: Dict[str, str]) -> Dict[str, bool]:
    """Test API connectivity for all providers."""
    print(f"\n🔧 STEP: API CONNECTIVITY TESTING")
    print("-" * 50)
    
    connectivity_results = {}
    
    # Test each unique provider
    tested_providers = set()
    for model in models:
        provider = model["provider"]
        if provider in tested_providers:
            continue
            
        tested_providers.add(provider)
        
        if provider not in api_keys:
            print(f"   ❌ {provider}: No API key configured")
            connectivity_results[provider] = False
            continue
        
        try:
            connected, error, latency = await LightweightAPITester.test_provider(provider, api_keys[provider])
            if connected:
                print(f"   ✅ {provider}: Connected (latency: {latency:.0f}ms)")
                connectivity_results[provider] = True
            else:
                print(f"   ❌ {provider}: Failed - {error}")
                connectivity_results[provider] = False
        except Exception as e:
            print(f"   ❌ {provider}: Exception - {str(e)}")
            connectivity_results[provider] = False
    
    successful_connections = sum(connectivity_results.values())
    total_providers = len(connectivity_results)
    print(f"\n   📊 API Connectivity: {successful_connections}/{total_providers} providers connected")
    
    return connectivity_results

async def validate_model_names(models: List[Dict[str, str]], api_keys: Dict[str, str], connectivity_results: Dict[str, bool]) -> Dict[str, bool]:
    """Validate individual model names by testing generation."""
    print(f"\n🧪 STEP: MODEL NAME VALIDATION")
    print("-" * 50)
    
    model_validation_results = {}
    
    # Only test models where provider connectivity succeeded
    for i, model in enumerate(models, 1):
        provider = model["provider"]
        model_name = model["model_name"]
        model_key = f"{provider}/{model_name}"
        
        if not connectivity_results.get(provider, False):
            print(f"   ⏭️  [{i:2d}/13] {model_key}: Skipped (provider not connected)")
            model_validation_results[model_key] = False
            continue
        
        try:
            # Create temporary evaluator to test the specific model
            model_config = {
                "provider": provider,
                "model_name": model_name,
                "temperature": 0.7,
            }
            
            # Provider-specific adjustments for validation (small test)
            if provider == "openai" and (model_name.startswith("o3") or model_name.startswith("o4")):
                model_config["max_completion_tokens"] = 50
            else:
                model_config["max_tokens"] = 50
            
            # Test the model with a simple generation
            test_evaluator = APIEvaluator(f"test-{provider}-{model_name}", model_config, api_keys)
            setup_success = await test_evaluator.setup()
            
            if setup_success:
                # Try a simple generation to validate the model name
                test_result = await test_evaluator.generate_response(
                    prompt="Say 'Hello' in one word.",
                    temperature=1.0,
                    max_tokens=10
                )
                
                if test_result and "response" in test_result:
                    print(f"   ✅ [{i:2d}/13] {model_key}: Valid")
                    model_validation_results[model_key] = True
                else:
                    print(f"   ❌ [{i:2d}/13] {model_key}: No response generated")
                    model_validation_results[model_key] = False
            else:
                print(f"   ❌ [{i:2d}/13] {model_key}: Setup failed")
                model_validation_results[model_key] = False
                
            # Clean up
            await test_evaluator.cleanup()
            
        except Exception as e:
            print(f"   ❌ [{i:2d}/13] {model_key}: Exception - {str(e)}")
            model_validation_results[model_key] = False
        
        # Small delay to avoid rate limits
        await asyncio.sleep(1)
    
    valid_models = sum(model_validation_results.values())
    total_models = len(models)
    print(f"\n   📊 Model Validation: {valid_models}/{total_models} models valid")
    
    return model_validation_results

async def fetch_prompts_from_directus() -> Tuple[Any, int]:
    """Fetch prompts from Directus CMS."""
    print(f"\n📝 STEP: FETCH PROMPTS FROM DIRECTUS")
    print("-" * 50)
    
    directus_client = DirectusClient()
    
    # Test Directus connection
    if not await directus_client.test_connection():
        raise Exception("Failed to connect to Directus")
    print(f"   ✅ Connected to Directus at {os.getenv('DIRECTUS_URL')}")
    
    # Get latest published prompt version
    prompt_version = await directus_client.get_latest_published_version()
    if not prompt_version:
        raise Exception("No published prompt version found")
    
    prompts = await directus_client.convert_to_storybench_format(prompt_version)
    if not prompts or not prompts.sequences:
        raise Exception("Failed to fetch prompts from Directus")
    
    # Validate we have 5 sequences with 3 prompts each
    total_prompts = sum(len(seq) for seq in prompts.sequences.values())
    print(f"   📋 Found: v{prompt_version.version_number} - {prompt_version.version_name}")
    print(f"   📋 Sequences: {list(prompts.sequences.keys())}")
    print(f"   📋 Total prompts: {total_prompts}")
    
    if len(prompts.sequences) != 5:
        raise Exception(f"Expected 5 sequences, found {len(prompts.sequences)}")
    
    if total_prompts != 15:
        raise Exception(f"Expected 15 total prompts, found {total_prompts}")
    
    # Validate each sequence has 3 prompts
    for seq_name, seq_prompts in prompts.sequences.items():
        if len(seq_prompts) != 3:
            raise Exception(f"Sequence '{seq_name}' has {len(seq_prompts)} prompts, expected 3")
    
    print(f"   ✅ Validated: 5 sequences × 3 prompts = 15 total prompts")
    
    return prompts, prompt_version.version_number


async def fetch_evaluation_criteria_from_directus() -> Tuple[Any, int]:
    """Fetch evaluation criteria from Directus CMS."""
    print(f"\n🎯 STEP: FETCH EVALUATION CRITERIA FROM DIRECTUS")
    print("-" * 50)
    
    directus_client = DirectusClient()
    
    # Get latest published evaluation version
    eval_version = await directus_client.get_latest_published_evaluation_version()
    if not eval_version:
        raise Exception("No published evaluation version found")
    
    eval_criteria = await directus_client.convert_to_storybench_evaluation_format(eval_version)
    if not eval_criteria or not eval_criteria.criteria:
        raise Exception("Failed to fetch evaluation criteria from Directus")
    
    # Validate we have 7 criteria
    criteria_count = len(eval_criteria.criteria)
    print(f"   📋 Found: v{eval_version.version_number} - {eval_version.version_name}")
    print(f"   📋 Criteria: {list(eval_criteria.criteria.keys())}")
    print(f"   📋 Total criteria: {criteria_count}")
    
    if criteria_count != 7:
        raise Exception(f"Expected 7 evaluation criteria, found {criteria_count}")
    
    print(f"   ✅ Validated: 7 evaluation criteria")
    
    return eval_criteria, eval_version.version_number

async def setup_gemini_evaluator(api_keys: Dict[str, str]) -> APIEvaluator:
    """Setup Gemini 2.5 Pro evaluator."""
    print(f"\n🧠 STEP: SETUP GEMINI 2.5 PRO EVALUATOR")
    print("-" * 50)
    
    evaluator_config = {
        "provider": "gemini",
        "model_name": "gemini-2.5-pro-preview-05-06",
        "temperature": 0.3,
        "max_tokens": 8192
    }
    
    evaluator = APIEvaluator("gemini-2.5-pro-evaluator", evaluator_config, api_keys)
    evaluator_ready = await evaluator.setup()
    
    if not evaluator_ready:
        raise Exception("Failed to setup Gemini 2.5 Pro evaluator")
    
    print(f"   ✅ Gemini 2.5 Pro evaluator ready")
    return evaluator


def build_sequence_evaluation_prompt(sequence_responses: List[Dict], eval_criteria: Any) -> str:
    """Build evaluation prompt for a sequence of responses."""
    
    # Build criteria descriptions
    criteria_text = ""
    for criterion_name, criterion in eval_criteria.criteria.items():
        criteria_text += f"\n• {criterion_name}: {criterion.description} (Scale: {criterion.scale[0]}-{criterion.scale[1]})"
    
    # Build sequence context
    sequence_context = ""
    for i, response in enumerate(sequence_responses, 1):
        sequence_context += f"""
=== RESPONSE {i}: {response['prompt_name']} ===
PROMPT: {response['prompt_text']}

RESPONSE: {response['text']}
"""
    
    model_name = sequence_responses[0]['model_name']
    sequence_name = sequence_responses[0]['sequence_name']
    run = sequence_responses[0]['run']
    
    prompt = f"""Evaluate this {len(sequence_responses)}-response creative writing sequence for coherence and quality.

MODEL: {model_name} | SEQUENCE: {sequence_name} | RUN: {run}

EVALUATION CRITERIA:
{criteria_text}

SCORING GUIDELINES:
{eval_criteria.scoring_guidelines}

SEQUENCE TO EVALUATE:
{sequence_context}

INSTRUCTIONS:
Evaluate each response individually AND as part of the sequence. Pay special attention to COHERENCE - how well each response builds upon and connects with previous responses. Provide detailed feedback for each criterion.

Please provide your evaluation in this format for each response:

RESPONSE 1 EVALUATION:
[criterion_name]: [score] - [detailed justification]
[continue for all criteria...]

RESPONSE 2 EVALUATION:
[criterion_name]: [score] - [detailed justification]
[continue for all criteria...]

RESPONSE 3 EVALUATION:
[criterion_name]: [score] - [detailed justification]
[continue for all criteria...]

SEQUENCE COHERENCE ASSESSMENT:
[Overall assessment of how well the responses work together as a coherent narrative]"""
    
    return prompt

async def run_full_production_pipeline():
    """Run the complete production pipeline."""
    start_time = datetime.now()
    
    print("\n" + "=" * 80)
    print(" FULL API PRODUCTION TEST")
    print(" 12 Models × 15 Prompts × 3 Runs = 540 Responses + Evaluations")
    print("=" * 80)
    print(" 🌟 Models: 12 from test plan specification")
    print(" 📝 Prompts: 15 from Directus (5 sequences × 3 prompts)")
    print(" 🔄 Runs: 3 per sequence (context reset between sequences)")
    print(" 🌡️  Temperature: 1.0 for prompts, 0.3 for evaluation")
    print(" 🎯 Evaluation: Gemini-2.5-Pro with 7 criteria from Directus")
    print(" 💾 Storage: MongoDB Atlas")
    print("")
    
    test_results = {
        "status": "in_progress",
        "test_type": "full_api_production_pipeline",
        "pipeline_config": {
            "models_count": 12,
            "prompts_count": 15,
            "runs_per_sequence": 3,
            "sequences_count": 5,
            "prompt_temperature": 1.0,
            "evaluation_temperature": 0.3,
            "evaluator": "gemini-2.5-pro-preview-05-06",
            "criteria_count": 7
        },
        "responses": [],
        "evaluations": [],
        "performance": {},
        "validation_results": {},
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # STEP 1: Environment validation
        validate_environment()
        
        # STEP 2: Load and validate models
        models, api_keys = await load_and_validate_models()
        
        # STEP 3: Test API connectivity
        connectivity_results = await test_api_connectivity(models, api_keys)
        
        # STEP 4: Validate model names
        model_validation_results = await validate_model_names(models, api_keys, connectivity_results)
        
        # STEP 5: Fetch prompts from Directus
        prompts, prompt_version = await fetch_prompts_from_directus()
        
        # STEP 6: Fetch evaluation criteria from Directus
        eval_criteria, eval_version = await fetch_evaluation_criteria_from_directus()
        
        # STEP 7: Setup evaluator
        evaluator = await setup_gemini_evaluator(api_keys)
        
        # STEP 8: Setup database
        print(f"\n💾 STEP: DATABASE CONNECTION")
        print("-" * 50)
        
        db_connection = DatabaseConnection()
        database = await db_connection.connect(
            connection_string=os.getenv("MONGODB_URI"),
            database_name="storybench"
        )
        print(f"   ✅ Connected to MongoDB storybench database")
        
        responses_collection = database["responses"]
        evaluations_collection = database["response_llm_evaluations"]
        
        test_batch_id = f"full_api_prod_{int(datetime.now().timestamp())}"
        
        # Store validation results
        test_results["validation_results"] = {
            "api_connectivity": connectivity_results,
            "model_validation": model_validation_results,
            "prompt_version": prompt_version,
            "eval_version": eval_version,
            "valid_models": sum(model_validation_results.values()),
            "total_models": len(models)
        }
        
        # STEP 9: Execute pipeline
        print(f"\n🚀 STEP: EXECUTE PRODUCTION PIPELINE")
        print("-" * 50)
        
        # Filter to only valid models and continue with any working models
        valid_models = [m for m in models if model_validation_results.get(f"{m['provider']}/{m['model_name']}", False)]
        
        expected_total_responses = len(valid_models) * 15 * 3
        print(f"   Target: {len(valid_models)} models × {len(prompts.sequences)} sequences × 3 runs = {len(valid_models) * len(prompts.sequences) * 3} sequence runs")
        print(f"   Total responses expected: {expected_total_responses}")
        print(f"   Using {len(valid_models)} validated models (skipping failed models)")
        
        if not valid_models:
            raise Exception("No valid models available for testing")
        
        total_generation_time = 0
        total_evaluation_time = 0
        successful_responses = 0
        successful_evaluations = 0
        
        # Process each valid model
        for model_idx, model in enumerate(valid_models, 1):
            provider = model["provider"]
            model_name = model["model_name"]
            model_key = f"{provider}/{model_name}"
            
            print(f"\n   🤖 MODEL {model_idx}/{len(valid_models)}: {model_key}")
            
            # Create model-specific generator
            model_config = {
                "provider": provider,
                "model_name": model_name,
                "temperature": 1.0,
            }
            
            # Provider-specific adjustments - Higher token limits for actual generation
            if provider == "openai" and (model_name.startswith("o3") or model_name.startswith("o4")):
                model_config["max_completion_tokens"] = 8192
            else:
                model_config["max_tokens"] = 8192
            
            generator = APIEvaluator(f"{provider}-{model_name}-generator", model_config, api_keys)
            generator_ready = await generator.setup()
            
            if not generator_ready:
                print(f"      ❌ Failed to setup generator")
                continue
            
            # Process each sequence (with 3 runs per sequence)
            for sequence_name, sequence_prompts in prompts.sequences.items():
                for run in range(1, 4):  # 3 runs per sequence
                    print(f"      📝 Sequence: {sequence_name}, Run {run}/3")
                    
                    sequence_responses = []
                    
                    # Process all 3 prompts in the sequence (maintaining context for coherence)
                    for prompt_idx, prompt in enumerate(sequence_prompts, 1):
                        try:
                            print(f"         🔤 Prompt {prompt_idx}/3: {prompt.name}")
                            
                            # GENERATION PHASE
                            gen_start = datetime.now()
                            response_result = await generator.generate_response(
                                prompt=prompt.text,
                                temperature=1.0,
                                max_tokens=8192
                            )
                            
                            if not response_result or "response" not in response_result:
                                print(f"            ❌ No response generated - SKIPPING to next model")
                                # Skip remaining prompts for this model and go to next model
                                break
                            
                            response_text = response_result["response"]
                            generation_time = response_result.get("generation_time", 0)
                            total_generation_time += generation_time
                            
                            print(f"            ✅ Generated: {len(response_text)} chars ({generation_time:.2f}s)")
                            
                            # Store response in MongoDB
                            response_doc = {
                                "text": response_text,
                                "prompt_name": prompt.name,
                                "sequence_name": sequence_name,
                                "model_name": model_name,
                                "model_type": "api",
                                "model_provider": provider,
                                "settings": model_config,
                                "created_at": datetime.utcnow(),
                                "generation_time": generation_time,
                                "test_run": True,
                                "test_batch": test_batch_id,
                                "prompt_index": prompt_idx,
                                "run": run,
                                "prompt_text": prompt.text,
                                "sequence": sequence_name
                            }
                            
                            insert_result = await responses_collection.insert_one(response_doc)
                            response_doc["_id"] = str(insert_result.inserted_id)
                            test_results["responses"].append(response_doc)
                            sequence_responses.append(response_doc)
                            successful_responses += 1
                            
                        except Exception as e:
                            error_msg = f"Error generating response for {model_key}, {sequence_name}, run {run}, prompt {prompt_idx}: {str(e)}"
                            print(f"            ❌ {error_msg}")
                            test_results["errors"].append(error_msg)
                            # Skip remaining prompts for this model and go to next model
                            print(f"            ⏭️  Skipping to next model due to API problem")
                            break
                    
                    # EVALUATION PHASE - Evaluate the complete sequence
                    if sequence_responses:
                        try:
                            print(f"         🎯 Evaluating sequence ({len(sequence_responses)} responses)")
                            
                            eval_start = datetime.now()
                            
                            # Build evaluation prompt for the sequence
                            eval_prompt = build_sequence_evaluation_prompt(sequence_responses, eval_criteria)
                            
                            evaluation_result = await evaluator.generate_response(
                                prompt=eval_prompt,
                                temperature=0.3,
                                max_tokens=8192
                            )
                            
                            evaluation_text = evaluation_result.get("response", "")
                            evaluation_time = (datetime.now() - eval_start).total_seconds()
                            total_evaluation_time += evaluation_time
                            
                            print(f"            ✅ Evaluated: {len(evaluation_text)} chars ({evaluation_time:.2f}s)")
                            
                            # Parse and store evaluations for each response in the sequence
                            for response_doc in sequence_responses:
                                evaluation_doc = {
                                    "response_id": response_doc["_id"],
                                    "evaluating_llm_provider": "gemini",
                                    "evaluating_llm_model": "gemini-2.5-pro-preview-05-06",
                                    "evaluation_criteria_version": f"directus_v{eval_version}",
                                    "evaluation_text": evaluation_text,
                                    "evaluation_time": evaluation_time,
                                    "created_at": datetime.utcnow(),
                                    "test_run": True,
                                    "test_batch": test_batch_id
                                }
                                
                                eval_insert = await evaluations_collection.insert_one(evaluation_doc)
                                evaluation_doc["_id"] = str(eval_insert.inserted_id)
                                test_results["evaluations"].append(evaluation_doc)
                                successful_evaluations += 1
                        
                        except Exception as e:
                            error_msg = f"Error evaluating sequence for {model_key}, {sequence_name}, run {run}: {str(e)}"
                            print(f"         ❌ {error_msg}")
                            test_results["errors"].append(error_msg)
                    
                    # Small delay between sequence runs
                    await asyncio.sleep(2)
            
            # Clean up generator
            await generator.cleanup()
            print(f"      ✅ Model {model_key} completed")
        
        # STEP 10: Finalize results
        total_time = (datetime.now() - start_time).total_seconds()
        
        test_results["performance"] = {
            "total_time": total_time,
            "total_generation_time": total_generation_time,
            "total_evaluation_time": total_evaluation_time,
            "successful_responses": successful_responses,
            "successful_evaluations": successful_evaluations,
            "expected_responses": expected_total_responses,
            "expected_evaluations": expected_total_responses,
            "response_success_rate": successful_responses / expected_total_responses if expected_total_responses > 0 else 0,
            "evaluation_success_rate": successful_evaluations / expected_total_responses if expected_total_responses > 0 else 0
        }
        
        # Clean up
        await evaluator.cleanup()
        await db_connection.disconnect()
        
        # Determine final status
        if successful_responses == expected_total_responses and successful_evaluations == expected_total_responses:
            test_results["status"] = "complete_success"
            print(f"\n🎉 PRODUCTION PIPELINE: COMPLETE SUCCESS!")
            print("=" * 80)
            print(" ✅ All models validated and tested")
            print(" ✅ All prompts fetched from Directus")
            print(" ✅ All evaluation criteria fetched from Directus")
            print(" ✅ All responses generated and stored")
            print(" ✅ All evaluations completed and stored")
            print(" 🚀 Full API production pipeline validated")
        else:
            test_results["status"] = "partial_success"
            print(f"\n⚠️  PRODUCTION PIPELINE: PARTIAL SUCCESS")
            print("=" * 80)
            print(f" ✅ {successful_responses}/{expected_total_responses} responses generated")
            print(f" ✅ {successful_evaluations}/{expected_total_responses} evaluations completed")
        
    except Exception as e:
        print(f"\n❌ PRODUCTION PIPELINE FAILED: {str(e)}")
        test_results["status"] = "failed"
        test_results["errors"].append(str(e))
        
        # Cleanup on error
        try:
            if 'evaluator' in locals():
                await evaluator.cleanup()
            if 'generator' in locals():
                await generator.cleanup()
            if 'db_connection' in locals():
                await db_connection.disconnect()
        except:
            pass
    
    finally:
        # Save test report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"full_api_production_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n📋 Full API production test report saved to: {report_file}")
        return test_results


if __name__ == "__main__":
    asyncio.run(run_full_production_pipeline())
