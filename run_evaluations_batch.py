#!/usr/bin/env python3
"""
Script to run LLM evaluations in batches with better progress reporting.
"""

import asyncio
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.services.llm_evaluation_service import LLMEvaluationService
from src.storybench.database.repositories.response_repo import ResponseRepository

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
    
    # Initialize services
    evaluation_service = LLMEvaluationService(database, openai_api_key)
    response_repo = ResponseRepository(database)
    
    try:
        # Get active evaluation criteria
        criteria_config = await evaluation_service.criteria_repo.find_active()
        if not criteria_config:
            print("❌ No active evaluation criteria found")
            return
        
        print(f"✅ Found active criteria: {list(criteria_config.criteria.keys())}")
        
        # Get all responses
        all_responses = await response_repo.find_many({})
        print(f"📊 Found {len(all_responses)} total responses")
        
        # Filter out already evaluated responses
        unevaluated_responses = []
        for response in all_responses:
            existing_evals = await evaluation_service.evaluation_repo.get_evaluations_by_response_id(response.id)
            if not existing_evals:
                unevaluated_responses.append(response)
        
        print(f"🎯 Found {len(unevaluated_responses)} unevaluated responses")
        
        if len(unevaluated_responses) == 0:
            print("✅ All responses already evaluated!")
            
            # Show summary
            summary = await evaluation_service.get_evaluation_summary()
            print(f"\n📈 Current Status:")
            print(f"   Total evaluations: {summary['total_evaluations']}")
            print(f"   Coverage: {summary['evaluation_coverage']:.1%}")
            return
        
        # Process in batches
        batch_size = 5  # Process 5 at a time
        total_processed = 0
        total_errors = 0
        
        print(f"\n🚀 Starting evaluation in batches of {batch_size}...")
        print("=" * 60)
        
        for batch_start in range(0, len(unevaluated_responses), batch_size):
            batch_end = min(batch_start + batch_size, len(unevaluated_responses))
            batch = unevaluated_responses[batch_start:batch_end]
            
            print(f"\n📦 Processing batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end} of {len(unevaluated_responses)})")
            
            for i, response in enumerate(batch):
                response_num = batch_start + i + 1
                print(f"\n🔍 [{response_num}/{len(unevaluated_responses)}] Evaluating:", flush=True)
                print(f"    Model: {response.model_name}")
                print(f"    Sequence: {response.sequence}")
                print(f"    Prompt: {response.prompt_name}")
                
                try:
                    evaluation = await evaluation_service.evaluate_single_response(response, criteria_config)
                    
                    if evaluation:
                        total_processed += 1
                        print(f"    ✅ Success! (Total: {total_processed})")
                        
                        # Show scores briefly
                        scores = [f"{ce.criterion_name}:{ce.score}" for ce in evaluation.criteria_results if ce.score is not None]
                        print(f"    📊 Scores: {', '.join(scores[:3])}...")
                    else:
                        total_errors += 1
                        print(f"    ❌ Failed (Total errors: {total_errors})")
                    
                    # Rate limiting delay
                    await asyncio.sleep(2)
                    
                except KeyboardInterrupt:
                    print(f"\n⚠️  Interrupted by user. Processed {total_processed} responses so far.")
                    raise
                except Exception as e:
                    total_errors += 1
                    print(f"    ❌ Error: {str(e)[:100]}...")
                    await asyncio.sleep(1)  # Shorter delay on error
            
            # Batch summary
            print(f"\n📊 Batch complete. Overall progress: {total_processed}/{len(unevaluated_responses)} ({total_processed/len(unevaluated_responses)*100:.1f}%)")
            
            # Save progress periodically
            if total_processed > 0 and total_processed % 10 == 0:
                print("💾 Saving progress checkpoint...")
                summary = await evaluation_service.get_evaluation_summary()
                with open(f"evaluation_progress_{total_processed}.json", "w") as f:
                    json.dump(summary, f, indent=2, default=str)
        
        print(f"\n🎉 Evaluation completed!")
        print(f"   Successfully processed: {total_processed}")
        print(f"   Errors: {total_errors}")
        print(f"   Success rate: {total_processed/(total_processed+total_errors)*100:.1f}%")
        
        # Final summary
        print(f"\n📈 Generating final summary...")
        summary = await evaluation_service.get_evaluation_summary()
        
        print(f"\n📋 Final Results:")
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
        
        # Save final results
        output_file = Path("final_evaluation_results.json")
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n💾 Final results saved to: {output_file}")
        
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
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())
