#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def test_results_direct():
    mongodb_uri = os.getenv('MONGODB_URI')
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.storybench
    
    # Get completed evaluations
    evaluations = []
    async for eval_doc in db.evaluations.find({'status': 'completed'}):
        evaluations.append(eval_doc)
    
    print(f'Found {len(evaluations)} completed evaluations')
    
    for evaluation in evaluations:
        evaluation_id = str(evaluation['_id'])
        print(f'Processing evaluation: {evaluation_id}')
        
        # Get models for this evaluation
        models = []
        async for model in db.responses.aggregate([
            {'$match': {'evaluation_id': evaluation_id}},
            {'$group': {'_id': '$model_name', 'count': {'$sum': 1}}}
        ]):
            models.append(model['_id'])
        print(f'  Models: {models}')
        
        # Get LLM evaluations for responses
        for model_name in models:
            responses = await db.responses.find({
                'evaluation_id': evaluation_id,
                'model_name': model_name
            }).to_list(None)
            
            response_ids = [resp['_id'] for resp in responses]
            
            llm_evaluations = await db.response_llm_evaluations.find({
                'response_id': {'$in': response_ids}
            }).to_list(None)
            
            # Calculate scores
            all_scores = []
            criteria_scores = {}
            
            for llm_eval in llm_evaluations:
                for criterion in llm_eval.get("criteria_results", []):
                    criterion_name = criterion.get("criterion_name")
                    score = criterion.get("score")
                    if criterion_name and score is not None:
                        if criterion_name not in criteria_scores:
                            criteria_scores[criterion_name] = []
                        criteria_scores[criterion_name].append(score)
                        all_scores.append(score)
            
            overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
            print(f'  {model_name}: {len(responses)} responses, {len(llm_evaluations)} evaluations, avg score: {overall_avg:.2f}')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_results_direct())
