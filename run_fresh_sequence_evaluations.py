#!/usr/bin/env python3
"""
Script to run fresh sequence-aware LLM evaluations after clearing old results.
This ensures all sequences are evaluated with the new stringent criteria.
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.services.sequence_evaluation_service import SequenceEvaluationService
from src.storybench.database.repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository
from src.storybench.database.repositories.criteria_repo import CriteriaRepository

async def main():
    # Load environment variables
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not mongodb_uri or not openai_api_key:
        print("❌ Missing required environment variables (MONGODB_URI, OPENAI_API_KEY)")
        return
    
    print("🔗 Connecting to database...")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    try:
        # Initialize services
        evaluation_repo = ResponseLLMEvaluationRepository(database)
        criteria_repo = CriteriaRepository(database)
        evaluation_service = SequenceEvaluationService(database, openai_api_key)
        
        print("🧹 Clearing old evaluations to ensure fresh start...")
        
        # Delete all existing evaluations using collection directly
        delete_result = await evaluation_repo.collection.delete_many({})
        print(f"   Deleted {delete_result.deleted_count} old evaluations")
        
        # Verify we have the new stringent criteria
        active_criteria = await criteria_repo.find_active()
        if not active_criteria:
            print("❌ No active evaluation criteria found!")
            return
        
        print(f"✅ Using criteria version {active_criteria.version} with {len(active_criteria.criteria)} criteria")
        
        # Show sample of stringent criteria
        sample_criterion = list(active_criteria.criteria.values())[0]
        if "1=" in sample_criterion.description:
            print("✅ Confirmed: Using stringent criteria with explicit score definitions")
        else:
            print("⚠️  Warning: Criteria may not be the updated stringent version")
        
        print(f"\n🚀 Starting fresh sequence evaluation...")
        
        # Run the evaluation
        results = await evaluation_service.evaluate_all_sequences()
        
        print(f"\n📊 Evaluation Results:")
        print(f"   Total sequences: {results['total_sequences']}")
        print(f"   Sequences evaluated: {results['sequences_evaluated']}")
        print(f"   Total evaluations created: {results['total_evaluations_created']}")
        print(f"   Errors: {len(results['errors'])}")
        
        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors']:
                print(f"   {error}")
        
        # Generate and save summary
        print(f"\n📈 Generating evaluation summary...")
        summary = await evaluation_service.get_evaluation_summary()
        
        # Save results
        output_data = {
            "evaluation_results": results,
            "summary": summary,
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "criteria_version": active_criteria.version,
            "criteria_hash": active_criteria.config_hash
        }
        
        with open("fresh_sequence_evaluation_results.json", "w") as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n📋 Fresh Evaluation Summary:")
        print(f"   Total evaluations: {summary['total_evaluations']}")
        print(f"   Coverage: {summary['evaluation_coverage']:.1%}")
        
        print(f"\n🏆 Model Performance by Sequence:")
        for model_sequence, stats in summary['model_sequence_statistics'].items():
            model_name = stats['model_name']
            sequence_name = stats['sequence_name']
            total_evals = stats['total_evaluations']
            
            print(f"\n   {model_name} - {sequence_name}:")
            print(f"     Evaluations: {total_evals}")
            
            for criterion, data in stats['criteria_scores'].items():
                avg_score = data['average']
                count = data['count']
                print(f"     {criterion}: {avg_score:.2f} (n={count})")
        
        print(f"\n💾 Detailed results saved to: fresh_sequence_evaluation_results.json")
        
        # Expected structure validation
        print(f"\n📊 Expected Structure:")
        print(f"   2 models × 5 sequences × 3 runs = 30 total sequences")
        print(f"   Each sequence has 3 prompts = 90 total responses")
        print(f"   Found {results['total_sequences']} sequences in database")
        
        if results['sequences_evaluated'] == results['total_sequences']:
            print(f"✅ All sequences successfully evaluated!")
        else:
            print(f"⚠️  Only {results['sequences_evaluated']}/{results['total_sequences']} sequences evaluated")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()
        print(f"\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
