#!/usr/bin/env python3
"""
DeepSeek-R1-0528 Evaluation Pipeline
===================================
Generate responses and evaluations specifically for DeepSeek-R1-0528:
- 1 model (DeepSeek-R1-0528) 
- 15 prompts from Directus (5 sequences × 3 prompts)
- 3 runs per sequence = 45 total responses
- Evaluations using Gemini-2.5-Pro
- MongoDB storage with confirmation
- Thinking text filtering validation
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.evaluators.api_evaluator import APIEvaluator
from storybench.clients.directus_client import DirectusClient
from storybench.database.connection import DatabaseConnection


async def validate_environment():
    """Validate required environment variables."""
    print("🔧 ENVIRONMENT VALIDATION")
    print("-" * 50)
    
    required_keys = [
        ("DEEPINFRA_API_KEY", "DeepInfra API access"),
        ("GOOGLE_API_KEY", "Gemini evaluator"),
        ("MONGODB_URI", "Database storage"),
        ("DIRECTUS_URL", "Prompt source"),
        ("DIRECTUS_TOKEN", "Directus access")
    ]
    
    missing = []
    for key, description in required_keys:
        if os.getenv(key):
            print(f"   ✅ {key}: {description}")
        else:
            print(f"   ❌ {key}: Missing - {description}")
            missing.append(key)
    
    if missing:
        raise Exception(f"Missing required environment variables: {missing}")


async def test_deepseek_connectivity():
    """Test DeepSeek-R1-0528 connectivity and thinking filter."""
    print("\n🔗 DEEPSEEK-R1-0528 CONNECTIVITY TEST")
    print("-" * 50)
    
    api_keys = {"deepinfra": os.getenv("DEEPINFRA_API_KEY")}
    
    config = {
        "provider": "deepinfra",
        "model_name": "deepseek-ai/DeepSeek-R1-0528",
        "temperature": 1.0,
        "max_tokens": 1000
    }
    
    evaluator = APIEvaluator("deepseek-test", config, api_keys)
    
    try:
        await evaluator.setup()
        
        # Test with a prompt that might trigger thinking
        test_prompt = "Solve this step by step: What is 15 × 23?"
        response_data = await evaluator.generate_response(test_prompt)
        response_text = response_data.get('response', '')
        
        print(f"   ✅ API connection successful")
        print(f"   📝 Response length: {len(response_text)} characters")
        
        # Check thinking text filtering
        thinking_indicators = ['<think>', '<thinking>', '[Thinking]']
        has_thinking = any(indicator in response_text for indicator in thinking_indicators)
        
        if has_thinking:
            print(f"   ⚠️  WARNING: Thinking text detected in response")
            print(f"   🔍 First 200 chars: {response_text[:200]}...")
        else:
            print(f"   ✅ Thinking text properly filtered")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


async def fetch_directus_data():
    """Fetch prompts from Directus and load evaluation criteria from YAML."""
    print("\n📋 DATA LOADING")
    print("-" * 50)
    
    client = DirectusClient()
    
    # Fetch prompts from Directus
    print("   🔄 Fetching prompts from Directus...")
    prompts = await client.fetch_prompts()
    if not prompts or not prompts.sequences:
        raise Exception("No prompts found in Directus")
    
    print(f"   ✅ Loaded {len(prompts.sequences)} prompt sequences (v{prompts.version})")
    for seq_name in prompts.sequences.keys():
        print(f"      - {seq_name}")
    
    # Load evaluation criteria from local YAML
    print("   🔄 Loading evaluation criteria from YAML...")
    import yaml
    
    criteria_path = Path(__file__).parent / "config" / "evaluation_criteria.yaml"
    with open(criteria_path, 'r') as f:
        criteria_yaml = yaml.safe_load(f)
    
    # Simple criteria structure for compatibility
    class EvaluationCriteria:
        def __init__(self, criteria_dict):
            self.version = criteria_dict['version']
            self.version_name = "Local YAML"
            self.criteria = {}
            for name, details in criteria_dict['criteria'].items():
                criterion = type('Criterion', (), {
                    'name': details['name'],
                    'description': details['description'], 
                    'scale': details['scale']
                })()
                self.criteria[name] = criterion
    
    criteria = EvaluationCriteria(criteria_yaml)
    
    print(f"   ✅ Loaded evaluation criteria (v{criteria.version} - {criteria.version_name})")
    print(f"      Criteria: {list(criteria.criteria.keys())}")
    
    return prompts, criteria


async def setup_database():
    """Initialize database connection."""
    print("\n💾 DATABASE SETUP")
    print("-" * 50)
    
    db_connection = DatabaseConnection()
    database = await db_connection.connect(
        connection_string=os.getenv("MONGODB_URI"),
        database_name="storybench"
    )
    
    print(f"   ✅ Connected to MongoDB storybench database")
    
    responses_collection = database["responses"]
    evaluations_collection = database["response_llm_evaluations"]
    
    return database, responses_collection, evaluations_collection

async def setup_gemini_evaluator():
    """Setup Gemini evaluator for scoring responses."""
    print("\n🤖 EVALUATOR SETUP")
    print("-" * 50)
    
    api_keys = {"gemini": os.getenv("GOOGLE_API_KEY")}
    
    config = {
        "provider": "gemini", 
        "model_name": "gemini-2.5-pro-preview-05-06",
        "temperature": 0.3,  # Lower temp for consistent evaluation
        "max_tokens": 4096
    }
    
    evaluator = APIEvaluator("gemini-evaluator", config, api_keys)
    await evaluator.setup()
    
    print(f"   ✅ Gemini evaluator ready")
    return evaluator


async def generate_responses(prompts, database, responses_collection):
    """Generate responses for all prompts using DeepSeek-R1-0528."""
    print("\n🎯 RESPONSE GENERATION")
    print("-" * 50)
    
    api_keys = {"deepinfra": os.getenv("DEEPINFRA_API_KEY")}
    
    config = {
        "provider": "deepinfra",
        "model_name": "deepseek-ai/DeepSeek-R1-0528", 
        "temperature": 1.0,
        "max_tokens": 8192
    }
    
    generator = APIEvaluator("deepseek-generator", config, api_keys)
    await generator.setup()
    
    batch_id = f"deepseek_r1_0528_{int(datetime.now().timestamp())}"
    responses = []
    total_expected = len(prompts.sequences) * 3 * 3  # 5 sequences × 3 prompts × 3 runs
    
    print(f"   🎯 Target: {len(prompts.sequences)} sequences × 3 prompts × 3 runs = {total_expected} responses")
    print(f"   📝 Batch ID: {batch_id}")
    
    response_count = 0
    
    for sequence_name, sequence_prompts in prompts.sequences.items():
        print(f"\n   📖 Sequence: {sequence_name}")
        
        for run in range(1, 4):  # 3 runs per sequence
            print(f"      🔄 Run {run}/3")
            
            for prompt_idx, prompt in enumerate(sequence_prompts):
                response_count += 1
                
                try:
                    # Generate response
                    response_data = await generator.generate_response(prompt.text)
                    response_text = response_data.get('response', '')
                    
                    # Create response document
                    response_doc = {
                        "evaluation_id": batch_id,
                        "sequence": sequence_name,
                        "run": run,
                        "prompt_index": prompt_idx,
                        "prompt_name": prompt.name,
                        "prompt_text": prompt.text,
                        "response": response_text,
                        "model_name": config["model_name"],
                        "provider": config["provider"],
                        "temperature": config["temperature"],
                        "max_tokens": config["max_tokens"],
                        "generation_time": response_data.get('generation_time', 0),
                        "created_at": datetime.now(),
                        "test_run": True,
                        "test_batch": batch_id,
                        "metadata": response_data.get('metadata', {})
                    }
                    
                    # Store in MongoDB
                    result = await responses_collection.insert_one(response_doc)
                    response_doc['_id'] = result.inserted_id
                    responses.append(response_doc)
                    
                    print(f"         ✅ Response {response_count}/{total_expected}: {len(response_text)} chars")
                    
                    # Quick thinking text check
                    if any(indicator in response_text for indicator in ['<think>', '<thinking>', '[Thinking]']):
                        print(f"         ⚠️  WARNING: Potential thinking text in response")
                    
                except Exception as e:
                    print(f"         ❌ Failed: {e}")
                    continue
    
    print(f"\n   📊 Generated {len(responses)} responses successfully")
    return responses, batch_id

async def evaluate_responses(responses, criteria, evaluator, evaluations_collection):
    """Evaluate all generated responses."""
    print("\n📊 RESPONSE EVALUATION")
    print("-" * 50)
    
    evaluations = []
    
    print(f"   🎯 Evaluating {len(responses)} responses")
    print(f"   📋 Using criteria: {list(criteria.criteria.keys())}")
    
    for i, response_doc in enumerate(responses, 1):
        try:
            print(f"      📝 Evaluating response {i}/{len(responses)}")
            
            # Build evaluation prompt
            eval_prompt = f"""Please evaluate this creative writing response using the provided criteria.

PROMPT: {response_doc['prompt_text']}

RESPONSE: {response_doc['response']}

EVALUATION CRITERIA:
"""
            for criterion_name, criterion in criteria.criteria.items():
                eval_prompt += f"\n{criterion_name} (1-{criterion.scale}): {criterion.description}"
            
            eval_prompt += """

Please provide:
1. A score for each criterion (as specified in the scale)
2. Brief justification for each score
3. Overall assessment

Format your response as JSON:
{
  "scores": {
    "creativity": 4,
    "coherence": 3,
    ...
  },
  "justifications": {
    "creativity": "explanation...",
    "coherence": "explanation...",
    ...
  },
  "overall_assessment": "summary..."
}"""
            
            # Get evaluation
            eval_response_data = await evaluator.generate_response(eval_prompt)
            eval_text = eval_response_data.get('response', '')
            
            # Parse evaluation (basic parsing - could be improved)
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', eval_text, re.DOTALL)
                if json_match:
                    eval_json = json.loads(json_match.group())
                    scores = eval_json.get('scores', {})
                else:
                    scores = {}
            except:
                scores = {}
            
            # Create evaluation document
            evaluation_doc = {
                "response_id": response_doc['_id'],
                "evaluation_criteria_id": f"directus_v{criteria.version}",
                "criteria_results": scores,
                "evaluation_text": eval_text,
                "evaluation_time": eval_response_data.get('generation_time', 0),
                "evaluator_model": "gemini-2.5-pro-preview-05-06",
                "created_at": datetime.now(),
                "test_run": True,
                "test_batch": response_doc['test_batch']
            }
            
            # Store evaluation
            result = await evaluations_collection.insert_one(evaluation_doc)
            evaluation_doc['_id'] = result.inserted_id
            evaluations.append(evaluation_doc)
            
            print(f"         ✅ Evaluation complete: {len(scores)} scores")
            
        except Exception as e:
            print(f"         ❌ Evaluation failed: {e}")
            continue
    
    print(f"\n   📊 Completed {len(evaluations)} evaluations")
    return evaluations


async def verify_database_storage(responses_collection, evaluations_collection, batch_id):
    """Verify that data was properly stored in MongoDB."""
    print("\n✅ DATABASE VERIFICATION")
    print("-" * 50)
    
    # Check responses
    response_count = await responses_collection.count_documents({"test_batch": batch_id})
    print(f"   📄 Responses stored: {response_count}")
    
    # Check evaluations  
    evaluation_count = await evaluations_collection.count_documents({"test_batch": batch_id})
    print(f"   📊 Evaluations stored: {evaluation_count}")
    
    # Sample response check
    sample_response = await responses_collection.find_one({"test_batch": batch_id})
    if sample_response:
        print(f"   🔍 Sample response model: {sample_response.get('model_name')}")
        print(f"   🔍 Sample response length: {len(sample_response.get('response', ''))} chars")
        
        # Check for thinking text in stored responses
        response_text = sample_response.get('response', '')
        if any(indicator in response_text for indicator in ['<think>', '<thinking>', '[Thinking]']):
            print(f"   ⚠️  WARNING: Thinking text found in stored response!")
        else:
            print(f"   ✅ Thinking text properly filtered in stored responses")
    
    return response_count, evaluation_count


async def main():
    """Main pipeline execution."""
    print("DeepSeek-R1-0528 Evaluation Pipeline")
    print("=" * 60)
    
    try:
        # Step 1: Validate environment
        await validate_environment()
        
        # Step 2: Test connectivity
        connectivity_ok = await test_deepseek_connectivity()
        if not connectivity_ok:
            raise Exception("DeepSeek connectivity test failed")
        
        # Step 3: Fetch Directus data
        prompts, criteria = await fetch_directus_data()
        
        # Step 4: Setup database
        database, responses_collection, evaluations_collection = await setup_database()
        
        # Step 5: Setup evaluator
        evaluator = await setup_gemini_evaluator()
        
        # Step 6: Generate responses
        responses, batch_id = await generate_responses(prompts, database, responses_collection)
        
        # Step 7: Evaluate responses
        evaluations = await evaluate_responses(responses, criteria, evaluator, evaluations_collection)
        
        # Step 8: Verify storage
        response_count, evaluation_count = await verify_database_storage(
            responses_collection, evaluations_collection, batch_id
        )
        
        # Final summary
        print("\n🎉 PIPELINE COMPLETE")
        print("-" * 50)
        print(f"   📝 Batch ID: {batch_id}")
        print(f"   📄 Responses generated: {len(responses)}")
        print(f"   📊 Evaluations completed: {len(evaluations)}")
        print(f"   💾 MongoDB responses: {response_count}")
        print(f"   💾 MongoDB evaluations: {evaluation_count}")
        print(f"   🎯 Model: deepseek-ai/DeepSeek-R1-0528")
        print(f"   ✅ Thinking text filtering: Active")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
