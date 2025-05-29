#!/usr/bin/env python3
"""
Storybench Test Readiness Validation
===================================
Pre-flight validation script to ensure all systems are ready for the full end-to-end test.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.clients.directus_client import DirectusClient
from storybench.database.connection import DatabaseConnection
from storybench.web.services.lightweight_api_test import LightweightAPITester


async def validate_environment():
    """Validate all environment requirements."""
    print("🔧 ENVIRONMENT VALIDATION")
    print("-" * 50)
    
    required_vars = {
        "DIRECTUS_URL": "Directus CMS URL",
        "DIRECTUS_TOKEN": "Directus API token", 
        "MONGODB_URI": "MongoDB connection string",
        "GOOGLE_API_KEY": "Google Gemini API key for evaluation",
        "ANTHROPIC_API_KEY": "Anthropic Claude API key",
        "OPENAI_API_KEY": "OpenAI GPT API key", 
        "DEEPINFRA_API_KEY": "Deepinfra API key"
    }
    
    missing = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({desc})")
        else:
            print(f"   ✅ {var}")
    
    if missing:
        print("\n❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("   ✅ All environment variables present")
    return True


async def validate_file_structure():
    """Validate required files exist."""
    print("\n📁 FILE STRUCTURE VALIDATION")
    print("-" * 50)
    
    required_files = [
        "api-models-list.txt",
        "test_full_api_production.py", 
        ".env",
        "src/storybench/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing required files: {missing_files}")
        return False
    
    print("   ✅ All required files present")
    return True


async def validate_model_count():
    """Validate model count against test plan."""
    print("\n🤖 MODEL COUNT VALIDATION")
    print("-" * 50)
    
    models_file = Path("api-models-list.txt")
    models = []
    current_provider = None
    
    with open(models_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.endswith(':'):
                current_provider = line[:-1]
            elif current_provider:
                models.append({
                    "provider": current_provider,
                    "model_name": line
                })
    
    print(f"   📋 Found {len(models)} models in api-models-list.txt")
    
    # Group by provider
    providers = {}
    for model in models:
        provider = model["provider"]
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model["model_name"])
    
    for provider, model_list in providers.items():
        print(f"   📦 {provider}: {len(model_list)} models")
        for model in model_list:
            print(f"      - {model}")
    
    # Check against test plan requirement
    test_plan_models = 12
    if len(models) == test_plan_models:
        print(f"   ✅ Model count matches test plan: {len(models)} models")
        return True
    else:
        print(f"   ⚠️  Model count mismatch: Found {len(models)}, test plan expects {test_plan_models}")
        print(f"   💡 Consider removing one model or updating test plan")
        return True  # Non-blocking warning


async def validate_api_connectivity():
    """Test API connectivity for all providers."""
    print("\n🌐 API CONNECTIVITY VALIDATION")
    print("-" * 50)
    
    api_keys = {
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "deepinfra": os.getenv("DEEPINFRA_API_KEY")
    }
    
    connectivity_results = {}
    
    for provider, api_key in api_keys.items():
        if not api_key:
            print(f"   ❌ {provider}: No API key configured")
            connectivity_results[provider] = False
            continue
        
        try:
            connected, error, latency = await LightweightAPITester.test_provider(provider, api_key)
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
    
    return successful_connections == total_providers


async def validate_directus_integration():
    """Test Directus integration."""
    print("\n📝 DIRECTUS INTEGRATION VALIDATION")
    print("-" * 50)
    
    try:
        directus_client = DirectusClient()
        
        # Test connection
        if not await directus_client.test_connection():
            print("   ❌ Failed to connect to Directus")
            return False
        
        print(f"   ✅ Connected to Directus at {os.getenv('DIRECTUS_URL')}")
        
        # Test prompts
        prompt_version = await directus_client.get_latest_published_version()
        if not prompt_version:
            print("   ❌ No published prompt version found")
            return False
        
        prompts = await directus_client.convert_to_storybench_format(prompt_version)
        if not prompts or not prompts.sequences:
            print("   ❌ Failed to fetch prompts")
            return False
        
        # Validate prompt structure
        total_prompts = sum(len(seq) for seq in prompts.sequences.values())
        print(f"   📋 Prompts: v{prompt_version.version_number} - {prompt_version.version_name}")
        print(f"   📋 Sequences: {len(prompts.sequences)} (expected: 5)")
        print(f"   📋 Total prompts: {total_prompts} (expected: 15)")
        
        if len(prompts.sequences) != 5 or total_prompts != 15:
            print("   ❌ Incorrect prompt structure")
            return False
        
        # Test evaluation criteria
        eval_version = await directus_client.get_latest_published_evaluation_version()
        if not eval_version:
            print("   ❌ No published evaluation version found")
            return False
        
        eval_criteria = await directus_client.convert_to_storybench_evaluation_format(eval_version)
        if not eval_criteria or not eval_criteria.criteria:
            print("   ❌ Failed to fetch evaluation criteria")
            return False
        
        criteria_count = len(eval_criteria.criteria)
        print(f"   🎯 Evaluation: v{eval_version.version_number} - {eval_version.version_name}")
        print(f"   🎯 Criteria count: {criteria_count} (expected: 7)")
        
        if criteria_count != 7:
            print("   ❌ Incorrect evaluation criteria count")
            return False
        
        print("   ✅ Directus integration fully validated")
        return True
        
    except Exception as e:
        print(f"   ❌ Directus validation failed: {str(e)}")
        return False


async def validate_mongodb_connection():
    """Test MongoDB connection."""
    print("\n💾 MONGODB CONNECTION VALIDATION")
    print("-" * 50)
    
    try:
        db_connection = DatabaseConnection()
        database = await db_connection.connect(
            connection_string=os.getenv("MONGODB_URI"),
            database_name="storybench"
        )
        
        print(f"   ✅ Connected to MongoDB storybench database")
        
        # Test collections access
        responses_collection = database["responses"]
        evaluations_collection = database["response_llm_evaluations"]
        
        # Test write permissions with a test document
        test_doc = {
            "test": True,
            "timestamp": datetime.utcnow(),
            "validation_run": True
        }
        
        insert_result = await responses_collection.insert_one(test_doc)
        print(f"   ✅ Write permissions confirmed")
        
        # Clean up test document
        await responses_collection.delete_one({"_id": insert_result.inserted_id})
        print(f"   ✅ Cleanup successful")
        
        await db_connection.disconnect()
        return True
        
    except Exception as e:
        print(f"   ❌ MongoDB validation failed: {str(e)}")
        return False


async def calculate_expected_metrics():
    """Calculate expected test metrics."""
    print("\n📊 EXPECTED TEST METRICS")
    print("-" * 50)
    
    # Load model count
    models_file = Path("api-models-list.txt")
    model_count = 0
    with open(models_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.endswith(':'):
                model_count += 1
    
    sequences = 5
    prompts_per_sequence = 3
    runs_per_sequence = 3
    
    responses_per_model = sequences * prompts_per_sequence * runs_per_sequence  # 45
    total_responses = model_count * responses_per_model
    total_evaluations = total_responses  # 1 evaluation per response
    
    print(f"   🤖 Models: {model_count}")
    print(f"   📝 Sequences: {sequences}")
    print(f"   🔄 Runs per sequence: {runs_per_sequence}")
    print(f"   📊 Responses per model: {responses_per_model}")
    print(f"   📊 Total responses expected: {total_responses}")
    print(f"   🎯 Total evaluations expected: {total_evaluations}")
    
    # Estimate timing
    avg_response_time = 15  # seconds
    avg_evaluation_time = 10  # seconds
    
    total_generation_time = total_responses * avg_response_time
    total_evaluation_time = total_evaluations * avg_evaluation_time
    estimated_total_time = (total_generation_time + total_evaluation_time) / 60  # minutes
    
    print(f"   ⏱️  Estimated generation time: {total_generation_time/60:.1f} minutes")
    print(f"   ⏱️  Estimated evaluation time: {total_evaluation_time/60:.1f} minutes") 
    print(f"   ⏱️  Estimated total time: {estimated_total_time:.1f} minutes")
    
    return {
        "model_count": model_count,
        "total_responses": total_responses,
        "total_evaluations": total_evaluations,
        "estimated_time_minutes": estimated_total_time
    }


async def main():
    """Run complete validation."""
    print("=" * 80)
    print(" STORYBENCH END-TO-END TEST READINESS VALIDATION")
    print("=" * 80)
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "validations": {},
        "overall_status": "unknown"
    }
    
    # Run all validations
    validations = [
        ("environment", validate_environment),
        ("file_structure", validate_file_structure), 
        ("model_count", validate_model_count),
        ("api_connectivity", validate_api_connectivity),
        ("directus_integration", validate_directus_integration),
        ("mongodb_connection", validate_mongodb_connection)
    ]
    
    all_passed = True
    
    for name, validation_func in validations:
        try:
            result = await validation_func()
            validation_results["validations"][name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"\n❌ {name} validation failed with exception: {str(e)}")
            validation_results["validations"][name] = False
            all_passed = False
    
    # Calculate metrics
    metrics = await calculate_expected_metrics()
    validation_results["expected_metrics"] = metrics
    
    # Final status
    if all_passed:
        validation_results["overall_status"] = "ready"
        print("\n" + "=" * 80)
        print(" 🎉 VALIDATION COMPLETE: READY FOR FULL TEST")
        print("=" * 80)
        print(" ✅ All systems validated")
        print(" ✅ APIs connected")
        print(" ✅ Directus integration working")
        print(" ✅ MongoDB storage ready")
        print(f" 🚀 Expected: {metrics['total_responses']} responses in ~{metrics['estimated_time_minutes']:.0f} minutes")
        print("")
        print(" Run the full test with:")
        print(" python test_full_api_production.py")
    else:
        validation_results["overall_status"] = "not_ready"
        print("\n" + "=" * 80)
        print(" ❌ VALIDATION FAILED: NOT READY FOR FULL TEST")
        print("=" * 80)
        print(" Please fix the issues above before running the full test")
    
    # Save validation report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_readiness_validation_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"\n📋 Validation report saved to: {report_file}")
    return validation_results


if __name__ == "__main__":
    asyncio.run(main())
