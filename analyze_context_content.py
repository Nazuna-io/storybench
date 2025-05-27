#!/usr/bin/env python3
"""Analyze the exact context content that's causing the issue."""

import asyncio
import json
import os
import logging
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

import sys
sys.path.append('src')

from storybench.database.services.config_service import ConfigService
from storybench.evaluators.factory import EvaluatorFactory

async def analyze_context_content():
    """Analyze what's in the context that causes failure."""
    
    load_dotenv()
    
    # Connect to database and get prompts
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))  
    database = client["storybench"]
    config_service = ConfigService(database)
    prompts_config = await config_service.get_active_prompts()
    film_prompts = prompts_config.sequences.get('FilmNarrative', [])
    
    # Load and setup model
    with open('config/local_models.json', 'r') as f:
        local_config = json.load(f)
    model_data = local_config["models"][0]
    
    factory_config = {
        "type": "local",
        "provider": model_data.get("provider"),
        "repo_id": model_data.get("model_repo_id"),
        "filename": model_data.get("model_filename"),
        **model_data.get("model_settings", {})
    }
    
    evaluator = EvaluatorFactory.create_evaluator(
        name=model_data["name"],
        config=factory_config,
        api_keys={}
    )
    
    await evaluator.setup()
    
    # Generate first response
    first_prompt = film_prompts[0].text
    response1 = await evaluator.generate_response(first_prompt, max_tokens=1000)
    first_response = response1['text']
    
    print("🔍 ANALYZING PROBLEMATIC CONTEXT")
    print("=" * 60)
    print(f"First response length: {len(first_response)} chars")
    print(f"First response preview:")
    print(first_response[:500])
    print("..." if len(first_response) > 500 else "")
    print()
    
    # Check for problematic patterns
    second_prompt = film_prompts[1].text
    print(f"Second prompt: {second_prompt}")
    print()
    
    # Test different context joining methods
    contexts_to_test = [
        ("Direct concatenation", first_response + second_prompt),
        ("Double newline separator", first_response + "\n\n" + second_prompt),
        ("Explicit separator", first_response + "\n\n---\n\n" + second_prompt),
        ("Context marker", f"[Previous response:]\n{first_response}\n\n[New prompt:]\n{second_prompt}"),
        ("Clean truncation", first_response[-1000:] + "\n\n" + second_prompt),
    ]
    
    for name, context in contexts_to_test:
        print(f"🧪 Testing: {name}")
        print(f"   Length: {len(context)} chars")
        print(f"   Tokens: ~{len(context)//3}")
        
        try:
            if hasattr(evaluator, 'reset_model_state'):
                await evaluator.reset_model_state()
                
            response = await evaluator.generate_response(context, max_tokens=100)
            result_len = len(response['text'])
            print(f"   Result: {result_len} chars - {'✅ SUCCESS' if result_len > 10 else '❌ FAILED'}")
            if result_len > 10:
                print(f"   Preview: {response['text'][:100]}...")
        except Exception as e:
            print(f"   Result: ERROR - {e}")
        print()
    
    await evaluator.cleanup()

if __name__ == "__main__":
    asyncio.run(analyze_context_content())
