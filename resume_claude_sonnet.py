#!/usr/bin/env python3
"""
Resume test for claude-3-7-sonnet-20250219 model only
====================================================
This script resumes the production test for just the claude-3-7-sonnet-20250219 model
to complete its missing 18 responses and evaluations.
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


# RESUME TARGET - Only this model
RESUME_MODEL = {
    "provider": "anthropic", 
    "model_name": "claude-3-7-sonnet-20250219"
}

# Get the latest test batch ID to resume
async def get_latest_test_batch():
    """Get the latest test batch ID to resume from."""
    db_connection = DatabaseConnection()
    database = await db_connection.connect(
        connection_string=os.getenv("MONGODB_URI"),
        database_name="storybench"
    )
    
    # Find the most recent test batch
    responses_collection = database["responses"]
    latest_response = responses_collection.find({"test_run": True}).sort("created_at", -1).limit(1)
    
    batch_id = None
    async for doc in latest_response:
        batch_id = doc["test_batch"]
        break
    
    await db_connection.disconnect()
    return batch_id


async def check_model_progress(batch_id: str, model_name: str):
    """Check what responses are missing for the specific model."""
    db_connection = DatabaseConnection()
    database = await db_connection.connect(
        connection_string=os.getenv("MONGODB_URI"),
        database_name="storybench"
    )
    
    responses_collection = database["responses"]
    evaluations_collection = database["response_llm_evaluations"]
    
    # Find existing responses for this model
    existing_responses = []
    async for doc in responses_collection.find({
        "test_batch": batch_id,
        "model_name": model_name
    }):
        existing_responses.append({
            "sequence_name": doc["sequence_name"],
            "run": doc["run"],
            "prompt_index": doc["prompt_index"],
            "_id": str(doc["_id"])
        })
    
    # Find existing evaluations for this model
    pipeline = [
        {
            "$lookup": {
                "from": "responses",
                "localField": "response_id",
                "foreignField": "_id",
                "as": "response_doc"
            }
        },
        {
            "$unwind": "$response_doc"
        },
        {
            "$match": {
                "test_batch": batch_id,
                "response_doc.model_name": model_name
            }
        }
    ]
    
    existing_evaluations = []
    async for doc in evaluations_collection.aggregate(pipeline):
        existing_evaluations.append(str(doc["response_id"]))
    
    await db_connection.disconnect()
    
    print(f"📊 PROGRESS CHECK FOR {model_name}:")
    print(f"   Existing responses: {len(existing_responses)}/45")
    print(f"   Existing evaluations: {len(existing_evaluations)}/45")
    
    return existing_responses, existing_evaluations


async def resume_claude_sonnet():
    """Resume the test for claude-3-7-sonnet-20250219 only."""
    start_time = datetime.now()
    
    print("=" * 80)
    print(" RESUME: claude-3-7-sonnet-20250219")
    print("=" * 80)
    
    try:
        # Get latest test batch
        batch_id = await get_latest_test_batch()
        if not batch_id:
            print("❌ No previous test batch found to resume from")
            return
        
        print(f"🔄 Resuming test batch: {batch_id}")
        
        # Check current progress
        existing_responses, existing_evaluations = await check_model_progress(
            batch_id, RESUME_MODEL["model_name"]
        )
        
        if len(existing_responses) == 45:
            print("✅ All responses already completed!")
            return
        
        # Setup API keys
        api_keys = {
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "gemini": os.getenv("GOOGLE_API_KEY"),
            "deepinfra": os.getenv("DEEPINFRA_API_KEY")
        }
        
        # Setup database
        db_connection = DatabaseConnection()
        database = await db_connection.connect(
            connection_string=os.getenv("MONGODB_URI"),
            database_name="storybench"
        )
        responses_collection = database["responses"]
        evaluations_collection = database["response_llm_evaluations"]
        
        # Fetch prompts from Directus
        print(f"\n📝 FETCHING PROMPTS FROM DIRECTUS")
        print("-" * 50)
        
        directus_client = DirectusClient()
        
        # Test connection with retry
        connected = False
        for attempt in range(3):
            if await directus_client.test_connection():
                connected = True
                break
            print(f"   ⏳ Attempt {attempt + 1}/3 failed, retrying...")
            await asyncio.sleep(10)
        
        if not connected:
            raise Exception("Could not connect to Directus")
        
        prompt_version = await directus_client.get_latest_published_version()
        prompts = await directus_client.convert_to_storybench_format(prompt_version)
        print(f"   ✅ Loaded {len(prompts.sequences)} sequences")
        
        # Fetch evaluation criteria
        eval_version = await directus_client.get_latest_published_evaluation_version()
        eval_criteria = await directus_client.convert_to_storybench_evaluation_format(eval_version)
        print(f"   ✅ Loaded {len(eval_criteria.criteria)} evaluation criteria")
        
        # Setup evaluator for claude-3-7-sonnet
        print(f"\n🤖 SETTING UP CLAUDE-3-7-SONNET")
        print("-" * 50)
        
        generator_config = {
            "provider": RESUME_MODEL["provider"],
            "model_name": RESUME_MODEL["model_name"],
            "temperature": 1.0,
            "max_tokens": 8192
        }
        
        generator = APIEvaluator(f"resume-{RESUME_MODEL['model_name']}", generator_config, api_keys)
        if not await generator.setup():
            raise Exception("Failed to setup generator")
        
        print(f"   ✅ Generator ready")
        
        # Setup Gemini evaluator
        evaluator_config = {
            "provider": "gemini",
            "model_name": "gemini-2.5-pro-preview-05-06",
            "temperature": 0.3,
            "max_tokens": 8192
        }
        
        evaluator = APIEvaluator("resume-evaluator", evaluator_config, api_keys)
        if not await evaluator.setup():
            raise Exception("Failed to setup evaluator")
        
        print(f"   ✅ Evaluator ready")
        
        # Create lookup of existing responses
        existing_lookup = set()
        for resp in existing_responses:
            key = (resp["sequence_name"], resp["run"], resp["prompt_index"])
            existing_lookup.add(key)
        
        # Process missing responses
        print(f"\n🚀 GENERATING MISSING RESPONSES")
        print("-" * 50)
        
        new_responses = []
        successful_responses = 0
        
        for sequence_name, sequence_prompts in prompts.sequences.items():
            for run in range(1, 4):  # 3 runs per sequence
                for prompt_idx, prompt in enumerate(sequence_prompts, 1):
                    
                    # Check if this response already exists
                    key = (sequence_name, run, prompt_idx)
                    if key in existing_lookup:
                        continue
                    
                    try:
                        print(f"   🔤 {sequence_name} run {run}, prompt {prompt_idx}: {prompt.name}")
                        
                        # Generate response
                        response_result = await generator.generate_response(
                            prompt=prompt.text,
                            temperature=1.0,
                            max_tokens=8192
                        )
                        
                        if not response_result or "response" not in response_result:
                            print(f"      ❌ No response generated")
                            continue
                        
                        response_text = response_result["response"]
                        generation_time = response_result.get("generation_time", 0)
                        
                        # Store response in MongoDB
                        response_doc = {
                            "text": response_text,
                            "prompt_name": prompt.name,
                            "sequence_name": sequence_name,
                            "model_name": RESUME_MODEL["model_name"],
                            "model_type": "api",
                            "model_provider": RESUME_MODEL["provider"],
                            "settings": generator_config,
                            "created_at": datetime.utcnow(),
                            "generation_time": generation_time,
                            "test_run": True,
                            "test_batch": batch_id,
                            "prompt_index": prompt_idx,
                            "run": run,
                            "prompt_text": prompt.text,
                            "sequence": sequence_name
                        }
                        
                        insert_result = await responses_collection.insert_one(response_doc)
                        response_doc["_id"] = str(insert_result.inserted_id)
                        new_responses.append(response_doc)
                        successful_responses += 1
                        
                        print(f"      ✅ Generated: {len(response_text)} chars ({generation_time:.2f}s)")
                        
                    except Exception as e:
                        print(f"      ❌ Error: {str(e)}")
                        continue
        
        print(f"\n   📊 Generated {successful_responses} new responses")
        
        # Now evaluate all responses for this model (including existing ones)
        print(f"\n🎯 RUNNING EVALUATIONS")
        print("-" * 50)
        
        # Get all responses for this model in this batch
        all_responses = []
        async for doc in responses_collection.find({
            "test_batch": batch_id,
            "model_name": RESUME_MODEL["model_name"]
        }).sort([("sequence_name", 1), ("run", 1), ("prompt_index", 1)]):
            all_responses.append(doc)
        
        print(f"   📋 Found {len(all_responses)} total responses to evaluate")
        
        # Group responses by sequence and run for evaluation
        sequence_runs = {}
        for response in all_responses:
            key = (response["sequence_name"], response["run"])
            if key not in sequence_runs:
                sequence_runs[key] = []
            sequence_runs[key].append(response)
        
        successful_evaluations = 0
        
        for (sequence_name, run), sequence_responses in sequence_runs.items():
            if len(sequence_responses) != 3:
                print(f"   ⚠️  Skipping {sequence_name} run {run}: only {len(sequence_responses)}/3 responses")
                continue
            
            try:
                print(f"   🎯 Evaluating {sequence_name} run {run} ({len(sequence_responses)} responses)")
                
                # Build evaluation prompt
                criteria_text = ""
                for criterion_name, criterion in eval_criteria.criteria.items():
                    criteria_text += f"\n• {criterion_name}: {criterion.description}"
                
                sequence_text = ""
                for i, response in enumerate(sequence_responses, 1):
                    sequence_text += f"\n=== RESPONSE {i} ===\n{response['text']}\n"
                
                eval_prompt = f"""Evaluate this creative writing sequence using these 7 criteria:
{criteria_text}

SCORING GUIDELINES:
{eval_criteria.scoring_guidelines}

SEQUENCE TO EVALUATE:
{sequence_text}

Provide scores and detailed feedback for each criterion for each response."""
                
                # Generate evaluation
                eval_result = await evaluator.generate_response(
                    prompt=eval_prompt,
                    temperature=0.3,
                    max_tokens=8192
                )
                
                if eval_result and "response" in eval_result:
                    evaluation_text = eval_result["response"]
                    evaluation_time = eval_result.get("generation_time", 0)
                    
                    # Store evaluation for each response in the sequence
                    for response_doc in sequence_responses:
                        # Check if evaluation already exists
                        existing_eval = await evaluations_collection.find_one({
                            "response_id": response_doc["_id"],
                            "test_batch": batch_id
                        })
                        
                        if existing_eval:
                            continue  # Skip if evaluation already exists
                        
                        evaluation_doc = {
                            "response_id": response_doc["_id"],
                            "evaluating_llm_provider": "gemini",
                            "evaluating_llm_model": "gemini-2.5-pro-preview-05-06",
                            "evaluation_criteria_version": f"v{eval_version}",
                            "evaluation_text": evaluation_text,
                            "evaluation_time": evaluation_time,
                            "created_at": datetime.utcnow(),
                            "test_run": True,
                            "test_batch": batch_id
                        }
                        
                        await evaluations_collection.insert_one(evaluation_doc)
                        successful_evaluations += 1
                    
                    print(f"      ✅ Evaluated {len(sequence_responses)} responses")
                else:
                    print(f"      ❌ Evaluation failed")
                    
            except Exception as e:
                print(f"      ❌ Evaluation error: {str(e)}")
                continue
        
        # Cleanup
        await generator.cleanup()
        await evaluator.cleanup()
        await db_connection.disconnect()
        
        # Final status
        total_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n" + "=" * 80)
        print(" RESUME COMPLETE")
        print("=" * 80)
        print(f" ✅ New responses generated: {successful_responses}")
        print(f" ✅ New evaluations completed: {successful_evaluations}")
        print(f" ⏱️  Total time: {total_time/60:.1f} minutes")
        
        # Check final status
        final_responses, final_evaluations = await check_model_progress(
            batch_id, RESUME_MODEL["model_name"]
        )
        
        if len(final_responses) == 45 and len(final_evaluations) == 45:
            print(f" 🎉 claude-3-7-sonnet-20250219 NOW COMPLETE!")
        else:
            print(f" ⚠️  Still incomplete: {len(final_responses)}/45 responses, {len(final_evaluations)}/45 evaluations")
        
    except Exception as e:
        print(f"\n❌ RESUME FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(resume_claude_sonnet())
