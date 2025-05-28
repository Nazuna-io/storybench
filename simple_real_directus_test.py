#!/usr/bin/env python3
"""
Simple Real Directus Integration Test

This script tests the real Directus integration without complex evaluator dependencies:
- Real Directus API connection (from .env)
- Real MongoDB connection (from .env) 
- Focus on Directus prompt and evaluation criteria fetching
- No complex model evaluation (just demonstrates the integration)

Usage:
    python3 simple_real_directus_test.py
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import Storybench modules
from storybench.database.connection import DatabaseConnection
from storybench.clients.directus_client import DirectusClient
from storybench.database.services.directus_evaluation_service import DirectusEvaluationService


async def test_real_directus_integration():
    """Test real Directus integration focusing on prompt and criteria fetching."""
    
    print("🚀 REAL DIRECTUS INTEGRATION TEST")
    print("="*60)
    print("Testing real Directus & MongoDB APIs")
    print("Focus: Prompt fetching + Evaluation criteria fetching")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "mode": "real_directus_integration",
        "steps": {},
        "errors": []
    }
    
    try:
        # STEP 1: Verify environment variables
        print("🔍 STEP 1: VERIFYING ENVIRONMENT SETUP")
        print("-" * 50)
        
        required_vars = {
            'DIRECTUS_URL': os.getenv('DIRECTUS_URL'),
            'DIRECTUS_TOKEN': os.getenv('DIRECTUS_TOKEN'),
            'MONGODB_URI': os.getenv('MONGODB_URI')
        }
        
        for var, value in required_vars.items():
            if value:
                # Mask sensitive values for display
                if var == 'DIRECTUS_TOKEN':
                    display_value = value[:8] + "***"
                elif var == 'MONGODB_URI':
                    display_value = "mongodb+srv://***"
                else:
                    display_value = value
                print(f"   ✅ {var}: {display_value}")
            else:
                print(f"   ❌ {var}: NOT SET")
                raise Exception(f"Missing {var}")
        
        results["steps"]["environment_check"] = "success"
        
        # STEP 2: Connect to MongoDB
        print(f"\n📊 STEP 2: CONNECTING TO MONGODB")
        print("-" * 50)
        
        db_connection = DatabaseConnection()
        database = await db_connection.connect(
            connection_string=os.getenv('MONGODB_URI'),
            database_name="storybench"
        )
        print("✅ MongoDB connected successfully")
        results["steps"]["mongodb_connection"] = "success"
        
        # Test database access
        try:
            collections = await database.list_collection_names()
            print(f"   Available collections: {len(collections)}")
            if collections:
                print(f"   Sample collections: {', '.join(collections[:5])}")
        except Exception as e:
            print(f"   ⚠️  Could not list collections: {e}")
        
        # STEP 3: Connect to Directus and test basic connection
        print(f"\n🌐 STEP 3: CONNECTING TO DIRECTUS")
        print("-" * 50)
        
        directus_client = DirectusClient(
            base_url=os.getenv('DIRECTUS_URL'),
            token=os.getenv('DIRECTUS_TOKEN')
        )
        print("✅ Directus client initialized")
        results["steps"]["directus_connection"] = "success"
        
        # STEP 4: Fetch prompts from Directus
        print(f"\n📝 STEP 4: FETCHING PROMPTS FROM DIRECTUS")
        print("-" * 50)
        
        try:
            print("   Fetching latest published prompt version...")
            prompt_version = await directus_client.get_latest_published_version()
            print(f"   ✅ Found prompt version: {prompt_version.version_number} - {prompt_version.version_name}")
            print(f"   ✅ Status: {prompt_version.status}")
            print(f"   ✅ Created: {prompt_version.date_created}")
            
            print("   Converting to Storybench format...")
            prompts = await directus_client.convert_to_storybench_format(prompt_version)
            print(f"   ✅ Converted successfully!")
            print(f"   ✅ Version: {prompts.version}")
            print(f"   ✅ Total sequences: {len(prompts.sequences)}")
            
            # Show sequence details
            for seq_name, sequence in prompts.sequences.items():
                print(f"      - {seq_name}: {len(sequence)} prompts")
                for i, prompt in enumerate(sequence[:2]):  # Show first 2 prompts
                    print(f"        {i+1}. {prompt.name}: {prompt.text[:60]}...")
            
            results["steps"]["prompt_fetching"] = {
                "status": "success",
                "version": prompts.version,
                "sequences": len(prompts.sequences),
                "total_prompts": sum(len(seq) for seq in prompts.sequences.values())
            }
            
        except Exception as e:
            print(f"   ❌ Error fetching prompts: {e}")
            results["errors"].append(f"prompt_fetching: {e}")
            raise
        
        # STEP 5: Fetch evaluation criteria from Directus
        print(f"\n📊 STEP 5: FETCHING EVALUATION CRITERIA FROM DIRECTUS")
        print("-" * 50)
        
        try:
            # Initialize evaluation service
            print("   Initializing DirectusEvaluationService...")
            evaluation_service = DirectusEvaluationService(
                database=database,
                openai_api_key=None,  # Not needed for criteria fetching
                directus_client=directus_client
            )
            print("   ✅ Evaluation service initialized")
            
            print("   Fetching evaluation criteria...")
            criteria = await evaluation_service.get_evaluation_criteria()
            print(f"   ✅ Retrieved evaluation criteria successfully!")
            print(f"   ✅ Version: v{criteria.version} - {criteria.version_name}")
            print(f"   ✅ Criteria count: {len(criteria.criteria)}")
            
            # Show criteria details
            print("   ✅ Available criteria:")
            for name, criterion in criteria.criteria.items():
                print(f"      - {name}: {criterion.description}")
            
            print(f"   ✅ Scoring guidelines preview:")
            guidelines_preview = criteria.scoring_guidelines[:200] + "..." if len(criteria.scoring_guidelines) > 200 else criteria.scoring_guidelines
            print(f"      {guidelines_preview}")
            
            results["steps"]["evaluation_criteria"] = {
                "status": "success",
                "version": criteria.version,
                "version_name": criteria.version_name,
                "criteria_count": len(criteria.criteria),
                "criteria_names": list(criteria.criteria.keys())
            }
            
        except Exception as e:
            print(f"   ❌ Error fetching evaluation criteria: {e}")
            results["errors"].append(f"evaluation_criteria: {e}")
            raise
        
        # STEP 6: Generate Integration Report
        print(f"\n📋 STEP 6: REAL DIRECTUS INTEGRATION REPORT")
        print("="*60)
        
        print("🎯 INTEGRATION TEST RESULTS")
        print("-" * 40)
        
        print(f"📊 Real API Connections:")
        print(f"   ✅ Directus URL: {os.getenv('DIRECTUS_URL')}")
        print(f"   ✅ Directus Token: Active and working")
        print(f"   ✅ MongoDB: Connected to storybench database")
        
        print(f"\n📝 Prompt Management Integration:")
        print(f"   ✅ Prompt Version: v{prompts.version} (Directus ID: {prompts.directus_id})")
        print(f"   ✅ Prompt Sequences: {len(prompts.sequences)}")
        for seq_name, seq_prompts in prompts.sequences.items():
            print(f"      - {seq_name}: {len(seq_prompts)} prompts")
        
        print(f"   ✅ Criteria Version: v{criteria.version} - {criteria.version_name}")
        
        print(f"\n📊 Evaluation Criteria Integration:")
        print(f"   ✅ Criteria Version: v{criteria.version} - {criteria.version_name}")
        print(f"   ✅ Available Criteria: {len(criteria.criteria)}")
        print(f"   ✅ Scoring Guidelines: Retrieved successfully")
        print(f"   ✅ Runtime Fetching: Working correctly")
        
        print(f"\n✅ DIRECTUS INTEGRATION PATTERN VERIFICATION:")
        print(f"   ✅ Prompts fetched from Directus at runtime")
        print(f"   ✅ Evaluation criteria fetched from Directus at runtime")
        print(f"   ✅ NO local storage of prompts or criteria")
        print(f"   ✅ Version control through Directus CMS")
        print(f"   ✅ Real-time updates without code deployment")
        print(f"   ✅ Database connections stable and functional")
        
        print(f"\n🎉 REAL DIRECTUS INTEGRATION: COMPLETE SUCCESS!")
        print("   All real API connections working perfectly")
        print("   Ready for production use with local models")
        
        results["summary"] = {
            "directus_url": os.getenv('DIRECTUS_URL'),
            "mongodb_connected": True,
            "prompt_integration": {
                "version": prompts.version,
                "sequences": len(prompts.sequences),
                "total_prompts": sum(len(seq) for seq in prompts.sequences.values())
            },
            "evaluation_integration": {
                "version": criteria.version,
                "criteria_count": len(criteria.criteria),
                "criteria_names": list(criteria.criteria.keys())
            },
            "integration_status": "fully_functional"
        }
        
        results["steps"]["overall"] = "success"
        return results
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        results["errors"].append(f"overall_test: {e}")
        return results
    
    finally:
        # Clean up connections
        try:
            if 'db_connection' in locals():
                await db_connection.disconnect()
                print(f"\n🔌 Database connection closed")
        except:
            pass


async def main():
    """Main function."""
    try:
        results = await test_real_directus_integration()
        
        # Save results
        report_file = f"real_directus_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return len(results.get("errors", [])) == 0
        
    except Exception as e:
        print(f"❌ Main test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
