#!/usr/bin/env python3
"""
Compare Directus Schemas: Prompts vs Evaluation Criteria

This script compares the working prompt schema with the evaluation criteria schema
to identify any structural differences or setup issues.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.clients.directus_client import DirectusClient


async def compare_schemas():
    """Compare prompt and evaluation schemas in Directus."""
    
    print("🔍 DIRECTUS SCHEMA COMPARISON: PROMPTS vs EVALUATIONS")
    print("="*70)
    
    directus_client = DirectusClient(
        base_url=os.getenv('DIRECTUS_URL'),
        token=os.getenv('DIRECTUS_TOKEN')
    )
    
    comparison_results = {
        "timestamp": datetime.now().isoformat(),
        "prompt_schema": {},
        "evaluation_schema": {},
        "comparison": {}
    }
    
    try:
        # PART 1: ANALYZE PROMPT SCHEMA (WORKING)
        print("📝 PART 1: PROMPT SCHEMA ANALYSIS (WORKING)")
        print("="*50)
        
        # 1.1 Prompt Set Versions
        print("\n🔗 1.1 PROMPT_SET_VERSIONS")
        print("-" * 30)
        
        prompt_versions_response = await directus_client._make_request('GET', '/items/prompt_set_versions')
        prompt_versions = prompt_versions_response.get('data', [])
        
        print(f"Count: {len(prompt_versions)}")
        if prompt_versions:
            sample = prompt_versions[0]
            print(f"Sample fields: {list(sample.keys())}")
            print(f"Sample data:")
            for key, value in sample.items():
                if key in ['id', 'version_number', 'version_name', 'status', 'date_created']:
                    print(f"   {key}: {value}")
                elif key in ['sequences_in_set']:
                    print(f"   {key}: {type(value)} - {len(value) if isinstance(value, list) else value}")
        
        comparison_results["prompt_schema"]["versions"] = {
            "collection": "prompt_set_versions",
            "count": len(prompt_versions),
            "fields": list(prompt_versions[0].keys()) if prompt_versions else [],
            "sample": prompt_versions[0] if prompt_versions else None
        }
        
        # 1.2 Prompt Sequences
        print("\n📚 1.2 PROMPT_SEQUENCES")
        print("-" * 25)
        
        prompt_sequences_response = await directus_client._make_request('GET', '/items/prompt_sequences')
        prompt_sequences = prompt_sequences_response.get('data', [])
        
        print(f"Count: {len(prompt_sequences)}")
        if prompt_sequences:
            sample = prompt_sequences[0]
            print(f"Sample fields: {list(sample.keys())}")
            print(f"Sample data:")
            for key, value in sample.items():
                if key in ['id', 'sequence_name', 'status', 'date_created']:
                    print(f"   {key}: {value}")
                elif key in ['prompts_in_sequence']:
                    print(f"   {key}: {type(value)} - {len(value) if isinstance(value, list) else value}")
        
        comparison_results["prompt_schema"]["sequences"] = {
            "collection": "prompt_sequences",
            "count": len(prompt_sequences),
            "fields": list(prompt_sequences[0].keys()) if prompt_sequences else [],
            "sample": prompt_sequences[0] if prompt_sequences else None
        }
        
        # 1.3 Prompts
        print("\n📄 1.3 PROMPTS")
        print("-" * 15)
        
        prompts_response = await directus_client._make_request('GET', '/items/prompts')
        prompts = prompts_response.get('data', [])
        
        print(f"Count: {len(prompts)}")
        if prompts:
            sample = prompts[0]
            print(f"Sample fields: {list(sample.keys())}")
            print(f"Sample data:")
            for key, value in sample.items():
                if key in ['id', 'name', 'status', 'date_created']:
                    print(f"   {key}: {value}")
                elif key == 'text':
                    print(f"   {key}: {str(value)[:50]}...")
        
        comparison_results["prompt_schema"]["prompts"] = {
            "collection": "prompts",
            "count": len(prompts),
            "fields": list(prompts[0].keys()) if prompts else [],
            "sample": prompts[0] if prompts else None
        }
        
        # PART 2: ANALYZE EVALUATION SCHEMA (PROBLEMATIC)
        print("\n\n📊 PART 2: EVALUATION SCHEMA ANALYSIS (PROBLEMATIC)")
        print("="*55)
        
        # 2.1 Evaluation Versions
        print("\n🔗 2.1 EVALUATION_VERSIONS")
        print("-" * 30)
        
        eval_versions_response = await directus_client._make_request('GET', '/items/evaluation_versions')
        eval_versions = eval_versions_response.get('data', [])
        
        print(f"Count: {len(eval_versions)}")
        if eval_versions:
            sample = eval_versions[0]
            print(f"Sample fields: {list(sample.keys())}")
            print(f"Sample data:")
            for key, value in sample.items():
                if key in ['id', 'version_number', 'version_name', 'status', 'date_created']:
                    print(f"   {key}: {value}")
                elif key in ['evaluation_criteria_in_version', 'scoring_in_version']:
                    print(f"   {key}: {type(value)} - {len(value) if isinstance(value, list) else value}")
        
        comparison_results["evaluation_schema"]["versions"] = {
            "collection": "evaluation_versions",
            "count": len(eval_versions),
            "fields": list(eval_versions[0].keys()) if eval_versions else [],
            "sample": eval_versions[0] if eval_versions else None
        }
        
        # 2.2 Evaluation Criteria
        print("\n📚 2.2 EVALUATION_CRITERIA")
        print("-" * 30)
        
        eval_criteria_response = await directus_client._make_request('GET', '/items/evaluation_criteria')
        eval_criteria = eval_criteria_response.get('data', [])
        
        print(f"Count: {len(eval_criteria)}")
        if eval_criteria:
            sample = eval_criteria[0]
            print(f"Sample fields: {list(sample.keys())}")
            print(f"Sample data:")
            for key, value in sample.items():
                if key in ['id', 'name', 'status', 'date_created']:
                    print(f"   {key}: {value}")
                elif key == 'description':
                    print(f"   {key}: {str(value)[:50]}...")
        
        comparison_results["evaluation_schema"]["criteria"] = {
            "collection": "evaluation_criteria",
            "count": len(eval_criteria),
            "fields": list(eval_criteria[0].keys()) if eval_criteria else [],
            "sample": eval_criteria[0] if eval_criteria else None
        }
        
        # 2.3 Scoring
        print("\n📄 2.3 SCORING")
        print("-" * 15)
        
        scoring_response = await directus_client._make_request('GET', '/items/scoring')
        scoring = scoring_response.get('data', [])
        
        print(f"Count: {len(scoring)}")
        if scoring:
            sample = scoring[0]
            print(f"Sample fields: {list(sample.keys())}")
            print(f"Sample data:")
            for key, value in sample.items():
                if key in ['id', 'name', 'status', 'date_created']:
                    print(f"   {key}: {value}")
                elif key == 'guidelines':
                    print(f"   {key}: {str(value)[:50]}...")
        
        comparison_results["evaluation_schema"]["scoring"] = {
            "collection": "scoring",
            "count": len(scoring),
            "fields": list(scoring[0].keys()) if scoring else [],
            "sample": scoring[0] if scoring else None
        }
        
        # PART 3: JUNCTION TABLE ANALYSIS
        print("\n\n🔗 PART 3: JUNCTION TABLE ANALYSIS")
        print("="*40)
        
        # 3.1 Prompt Junction Tables (Working)
        print("\n✅ 3.1 PROMPT JUNCTION TABLES (WORKING)")
        print("-" * 40)
        
        junction_tables = [
            ('prompt_set_versions_prompt_sequences', 'Sequences in Set'),
            ('prompt_sequences_prompts', 'Prompts in Sequence')
        ]
        
        for table_name, description in junction_tables:
            try:
                junction_response = await directus_client._make_request('GET', f'/items/{table_name}')
                junction_data = junction_response.get('data', [])
                
                print(f"{description}: {len(junction_data)} connections")
                if junction_data:
                    sample = junction_data[0]
                    print(f"   Fields: {list(sample.keys())}")
                    print(f"   Sample: {sample}")
                
            except Exception as e:
                print(f"{description}: ❌ Error - {e}")
        
        # 3.2 Evaluation Junction Tables (Problematic?)
        print("\n❓ 3.2 EVALUATION JUNCTION TABLES (PROBLEMATIC?)")
        print("-" * 50)
        
        eval_junction_tables = [
            ('evaluation_versions_evaluation_criteria', 'Criteria in Version'),
            ('evaluation_versions_scoring', 'Scoring in Version')
        ]
        
        for table_name, description in eval_junction_tables:
            try:
                junction_response = await directus_client._make_request('GET', f'/items/{table_name}')
                junction_data = junction_response.get('data', [])
                
                print(f"{description}: {len(junction_data)} connections")
                if junction_data:
                    sample = junction_data[0]
                    print(f"   Fields: {list(sample.keys())}")
                    print(f"   Sample: {sample}")
                else:
                    print(f"   ⚠️  NO CONNECTIONS FOUND - This might be the issue!")
                
            except Exception as e:
                print(f"{description}: ❌ Error - {e}")
        
        # PART 4: COMPARISON SUMMARY
        print("\n\n📋 PART 4: SCHEMA COMPARISON SUMMARY")
        print("="*40)
        
        print("\n🔍 Key Differences Found:")
        
        # Compare version structures
        prompt_version_fields = set(comparison_results["prompt_schema"]["versions"]["fields"])
        eval_version_fields = set(comparison_results["evaluation_schema"]["versions"]["fields"])
        
        print(f"\n📊 Version Collections:")
        print(f"   Prompt versions fields: {len(prompt_version_fields)}")
        print(f"   Evaluation versions fields: {len(eval_version_fields)}")
        
        field_differences = prompt_version_fields.symmetric_difference(eval_version_fields)
        if field_differences:
            print(f"   ⚠️  Field differences: {field_differences}")
        else:
            print(f"   ✅ Field structures match")
        
        # Compare junction table setup
        print(f"\n🔗 Junction Table Setup:")
        print(f"   Prompt system: sequences_in_set → prompts_in_sequence")
        print(f"   Evaluation system: evaluation_criteria_in_version → scoring_in_version")
        print(f"   ⚠️  Junction tables might be empty for evaluation system")
        
        # Identify potential issues
        print(f"\n🎯 Potential Issues Identified:")
        print(f"   1. Junction tables may not be populated for evaluation versions")
        print(f"   2. Many-to-many relationships might not be properly configured")
        print(f"   3. The evaluation version might be missing required junction data")
        
        print(f"\n✅ SCHEMA COMPARISON COMPLETE")
        
        # Save results
        report_file = f"directus_schema_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed comparison saved to: {report_file}")
        
        return comparison_results
        
    except Exception as e:
        print(f"❌ Schema comparison failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(compare_schemas())
