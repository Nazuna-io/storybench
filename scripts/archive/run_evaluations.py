#!/usr/bin/env python3
"""
Script to run LLM evaluations on all stored responses.
"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.services.llm_evaluation_service import LLMEvaluationService

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    mongodb_uri = os.getenv("MONGODB_URI")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not mongodb_uri:
        print("❌ MONGODB_URI environment variable not set")
        return
    
    if not openai_api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key to run evaluations")
        return
    
    print("🔗 Connecting to database...")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    # Initialize evaluation service
    evaluation_service = LLMEvaluationService(database, openai_api_key)
    
    print("📊 Starting evaluation process...")
    
    try:
        # Run evaluations
        results = await evaluation_service.evaluate_all_responses()
        
        print("\n✅ Evaluation completed!")
        print(f"   Total responses: {results['total_responses']}")
        print(f"   Unevaluated responses: {results['unevaluated_responses']}")
        print(f"   Evaluations created: {results['evaluations_created']}")
        
        if results['errors']:
            print(f"   Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"     - {error}")
            if len(results['errors']) > 3:
                print(f"     ... and {len(results['errors']) - 3} more errors")
        
        # Get summary statistics
        print("\n📈 Getting evaluation summary...")
        summary = await evaluation_service.get_evaluation_summary()
        
        print(f"\n📋 Evaluation Summary:")
        print(f"   Total evaluations: {summary['total_evaluations']}")
        print(f"   Coverage: {summary['evaluation_coverage']:.1%}")
        
        print(f"\n🏆 Model Performance:")
        for model_name, stats in summary['model_statistics'].items():
            print(f"\n   {model_name}:")
            print(f"     Evaluations: {stats['total_evaluations']}")
            
            for criterion_name, criterion_stats in stats['criteria_scores'].items():
                if isinstance(criterion_stats, dict):
                    avg_score = criterion_stats['average']
                    count = criterion_stats['count']
                    print(f"     {criterion_name}: {avg_score:.2f} (n={count})")
        
        # Save detailed results to file
        output_file = Path("evaluation_results.json")
        with open(output_file, 'w') as f:
            json.dump({
                "evaluation_results": results,
                "summary": summary
            }, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection
        client.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
