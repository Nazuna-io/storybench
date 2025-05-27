#!/usr/bin/env python3
"""
Script to run sequence-aware LLM evaluations that properly assess coherence across related prompts.
"""

import asyncio
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.services.sequence_evaluation_service import SequenceEvaluationService

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
        return
    
    print("🔗 Connecting to database...")
    client = AsyncIOMotorClient(mongodb_uri)
    database = client["storybench"]
    
    # Initialize sequence evaluation service
    sequence_service = SequenceEvaluationService(database, openai_api_key)
    
    try:
        print("🧩 Starting sequence-aware evaluation...")
        print("   This approach evaluates complete sequences for proper coherence assessment")
        print("   Each sequence = 3 related prompts from the same model/sequence/run")
        print()
        
        # Run sequence evaluations
        results = await sequence_service.evaluate_all_sequences()
        
        print(f"\n✅ Sequence evaluation completed!")
        print(f"   Total sequences: {results['total_sequences']}")
        print(f"   Unevaluated sequences: {results['unevaluated_sequences']}")
        print(f"   Sequences evaluated: {results['sequences_evaluated']}")
        print(f"   Total evaluations created: {results['total_evaluations_created']}")
        
        if results['errors']:
            print(f"   Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"     - {error}")
            if len(results['errors']) > 3:
                print(f"     ... and {len(results['errors']) - 3} more errors")
        
        # Get summary statistics
        print(f"\n📈 Generating evaluation summary...")
        summary = await sequence_service.get_evaluation_summary()
        
        print(f"\n📋 Evaluation Summary:")
        print(f"   Total evaluations: {summary['total_evaluations']}")
        print(f"   Coverage: {summary['evaluation_coverage']:.1%}")
        
        print(f"\n🏆 Model Performance by Sequence:")
        for key, stats in summary['model_sequence_statistics'].items():
            model_name = stats['model_name']
            sequence_name = stats['sequence_name']
            
            print(f"\n   {model_name} - {sequence_name}:")
            print(f"     Evaluations: {stats['total_evaluations']}")
            
            for criterion_name, criterion_stats in stats['criteria_scores'].items():
                if isinstance(criterion_stats, dict):
                    avg_score = criterion_stats['average']
                    count = criterion_stats['count']
                    print(f"     {criterion_name}: {avg_score:.2f} (n={count})")
        
        # Save detailed results to file
        output_file = Path("sequence_evaluation_results.json")
        with open(output_file, 'w') as f:
            json.dump({
                "evaluation_results": results,
                "summary": summary
            }, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Calculate expected sequences
        print(f"\n📊 Expected Structure:")
        print(f"   2 models × 5 sequences × 3 runs = 30 total sequences")
        print(f"   Each sequence has 3 prompts = 90 total responses")
        print(f"   Found {results['total_sequences']} sequences in database")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection
        client.close()
        print(f"\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
