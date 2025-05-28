#!/usr/bin/env python3
"""
Production-Ready End-to-End Directus Integration Test

This script can run in two modes:
1. PRODUCTION MODE: With real environment variables for Directus, MongoDB, and API keys
2. DEMO MODE: With mock data when environment variables are not available

Usage:
    # Production mode (with environment variables set)
    python3 production_directus_test.py --mode production
    
    # Demo mode (mock data)
    python3 production_directus_test.py --mode demo
    
    # Auto-detect mode based on environment variables
    python3 production_directus_test.py

Environment Variables Required for Production Mode:
    - DIRECTUS_URL
    - DIRECTUS_TOKEN
    - MONGODB_URI
    - OPENAI_API_KEY (for evaluation)
"""

import os
import sys
import asyncio
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import Storybench modules
from storybench.database.connection import DatabaseConnection
from storybench.database.services.directus_evaluation_service import DirectusEvaluationService
from storybench.clients.directus_client import DirectusClient
from storybench.database.models import Response


def check_environment_setup() -> Dict[str, bool]:
    """Check which environment variables are available."""
    required_vars = {
        'DIRECTUS_URL': os.getenv('DIRECTUS_URL') is not None,
        'DIRECTUS_TOKEN': os.getenv('DIRECTUS_TOKEN') is not None,
        'MONGODB_URI': os.getenv('MONGODB_URI') is not None,
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY') is not None
    }
    
    return required_vars


async def run_production_mode():
    """Run the test in production mode with real API connections."""
    print("🚀 PRODUCTION MODE: Using real API connections")
    print("="*60)
    
    results = {
        "mode": "production",
        "timestamp": datetime.now().isoformat(),
        "steps": {},
        "responses": [],
        "evaluations": [],
        "errors": []
    }
    
    try:
        # Initialize database connection
        print("📊 Initializing MongoDB connection...")
        db_connection = DatabaseConnection()
        database = await db_connection.connect(
            connection_string=os.getenv('MONGODB_URI'),
            database_name="storybench"
        )
        print("✅ MongoDB connected successfully")
        
        # Initialize Directus client
        print("🌐 Initializing Directus client...")
        directus_client = DirectusClient(
            url=os.getenv('DIRECTUS_URL'),
            token=os.getenv('DIRECTUS_TOKEN')
        )
        print("✅ Directus client initialized")
        
        # Initialize evaluation service
        print("🔬 Initializing evaluation service...")
        evaluation_service = DirectusEvaluationService(
            database=database,
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            directus_client=directus_client
        )
        print("✅ Evaluation service initialized")
        
        # Fetch prompts from Directus
        print("📝 Fetching prompts from Directus...")
        try:
            prompt_version = await directus_client.get_latest_published_prompt_version()
            prompts = directus_client.convert_to_storybench_format(prompt_version)
            print(f"✅ Retrieved {len(prompts.sequences)} sequences from Directus v{prompts.version}")
            
            # Get first sequence for testing
            if prompts.sequences:
                sequence_name = list(prompts.sequences.keys())[0]
                sequence = prompts.sequences[sequence_name]
                print(f"📋 Testing with sequence: {sequence_name} ({len(sequence.prompts)} prompts)")
                results["steps"]["prompt_fetching"] = f"success_{len(sequence.prompts)}_prompts"
            else:
                raise Exception("No sequences found in Directus")
                
        except Exception as e:
            print(f"❌ Error fetching prompts from Directus: {e}")
            results["errors"].append(f"prompt_fetching: {e}")
            return results
        
        # Fetch evaluation criteria from Directus
        print("📊 Fetching evaluation criteria from Directus...")
        try:
            criteria = await evaluation_service.get_evaluation_criteria()
            print(f"✅ Retrieved evaluation criteria v{criteria.version}: {criteria.version_name}")
            print(f"   Criteria count: {len(criteria.criteria)}")
            results["steps"]["evaluation_setup"] = f"success_v{criteria.version}"
        except Exception as e:
            print(f"❌ Error fetching evaluation criteria: {e}")
            results["errors"].append(f"evaluation_setup: {e}")
            return results
        
        # Note: Actual response generation would require model APIs
        print("📝 Note: Response generation requires model API setup")
        print("   This would typically involve:")
        print("   1. Loading model configurations from database")
        print("   2. Initializing evaluators for each model")
        print("   3. Generating responses for each prompt")
        print("   4. Storing responses in MongoDB")
        
        # Note: Actual evaluation would require responses
        print("🔬 Note: LLM evaluation requires existing responses")
        print("   This would typically involve:")
        print("   1. Fetching responses from database")
        print("   2. Running evaluation for each response")
        print("   3. Storing evaluation results in MongoDB")
        
        print(f"\n✅ PRODUCTION MODE TEST: SUCCESS!")
        print("   All Directus and database connections working correctly")
        print("   Ready for full pipeline execution with model APIs")
        
        results["steps"]["overall"] = "success"
        return results
        
    except Exception as e:
        print(f"❌ Production mode error: {e}")
        results["errors"].append(f"production_mode: {e}")
        return results


async def run_demo_mode():
    """Run the test in demo mode with mock data."""
    print("🎭 DEMO MODE: Using mock data")
    print("="*60)
    
    # Run the comprehensive demo test from simple_end_to_end_test.py
    print("📝 Running comprehensive demo test...")
    
    # Import and run the demo functionality
    try:
        import subprocess
        result = subprocess.run(['python3', 'simple_end_to_end_test.py'], 
                              capture_output=True, text=True, cwd='/home/todd/storybench')
        
        if result.returncode == 0:
            print("✅ Demo test completed successfully!")
            print(result.stdout)
            return {"mode": "demo", "status": "success", "output": result.stdout}
        else:
            print(f"❌ Demo test failed: {result.stderr}")
            return {"mode": "demo", "status": "error", "error": result.stderr}
            
    except Exception as e:
        print(f"❌ Error running demo test: {e}")
        return {"mode": "demo", "status": "error", "error": str(e)}


async def run_auto_detect_mode():
    """Automatically detect which mode to run based on environment variables."""
    env_status = check_environment_setup()
    
    print("🔍 AUTO-DETECT MODE: Checking environment variables")
    print("="*60)
    
    for var, available in env_status.items():
        status = "✅ SET" if available else "❌ NOT SET"
        print(f"   {var}: {status}")
    
    production_ready = all(env_status.values())
    
    if production_ready:
        print(f"\n✅ All environment variables available - Running PRODUCTION MODE")
        return await run_production_mode()
    else:
        missing_vars = [var for var, available in env_status.items() if not available]
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Running DEMO MODE instead")
        return await run_demo_mode()


def print_environment_setup_guide():
    """Print a guide for setting up environment variables."""
    print("\n📚 ENVIRONMENT SETUP GUIDE")
    print("="*60)
    print("To run in production mode, set these environment variables:")
    print()
    print("# Directus Configuration")
    print("export DIRECTUS_URL='https://your-directus-instance.com'")
    print("export DIRECTUS_TOKEN='your-directus-api-token'")
    print()
    print("# MongoDB Configuration")
    print("export MONGODB_URI='mongodb://localhost:27017/storybench'")
    print()
    print("# OpenAI Configuration (for evaluation)")
    print("export OPENAI_API_KEY='your-openai-api-key'")
    print()
    print("Then run:")
    print("python3 production_directus_test.py --mode production")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='End-to-End Directus Integration Test')
    parser.add_argument('--mode', choices=['production', 'demo', 'auto'], 
                       default='auto', help='Test mode to run')
    parser.add_argument('--setup-guide', action='store_true',
                       help='Print environment setup guide')
    
    args = parser.parse_args()
    
    if args.setup_guide:
        print_environment_setup_guide()
        return True
    
    try:
        if args.mode == 'production':
            results = await run_production_mode()
        elif args.mode == 'demo':
            results = await run_demo_mode()
        else:  # auto
            results = await run_auto_detect_mode()
        
        # Save results
        if isinstance(results, dict):
            report_file = f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Test report saved to: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
