#!/usr/bin/env python3
"""Debug context building for local model."""

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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_context_issue():
    """Debug why context is failing on second prompt."""
    
    load_dotenv()
    
    # Connect to database
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))  
    database = client["storybench"]
    
    # Load prompts
    config_service = ConfigService(database)
    prompts_config = await config_service.get_active_prompts()
    film_prompts = prompts_config.sequences.get('FilmNarrative', [])
    
    # Load local model config
    with open('config/local_models.json', 'r') as f:
        local_config = json.load(f)
    
    model_data = local_config["models"][0]
    
    # Create evaluator
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
    
    print("🔧 Setting up model...")
    await evaluator.setup()
    print("✅ Model ready")
    
    # Test 1: Simple isolated prompt
    print("\n🧪 Test 1: Simple isolated prompt")
    simple_prompt = "Write a short story about a robot."
    try:
        response = await evaluator.generate_response(simple_prompt, max_tokens=100)
        print(f"✅ Simple prompt worked: {len(response['text'])} chars")
        print(f"Response: {response['text'][:200]}...")
    except Exception as e:
        print(f"❌ Simple prompt failed: {e}")
    
    # Test 2: First FilmNarrative prompt
    print(f"\n🧪 Test 2: First FilmNarrative prompt")
    first_prompt = film_prompts[0].text
    print(f"Prompt length: {len(first_prompt)} chars")
    
    try:
        response1 = await evaluator.generate_response(first_prompt, max_tokens=1000)
        print(f"✅ First prompt worked: {len(response1['text'])} chars")
        first_response_text = response1['text']
        print(f"Response preview: {first_response_text[:200]}...")
        
        # Reset model state
        if hasattr(evaluator, 'reset_model_state'):
            print("🔄 Resetting model state...")
            await evaluator.reset_model_state()
        
    except Exception as e:
        print(f"❌ First prompt failed: {e}")
        return
    
    # Test 3: Second prompt with context
    print(f"\n🧪 Test 3: Second prompt with context")
    second_prompt = film_prompts[1].text
    context_text = first_response_text + "\n\n" + second_prompt
    
    print(f"Context length: {len(context_text)} chars")
    print(f"Estimated tokens: {len(context_text) // 3}")
    print(f"Context preview: ...{context_text[-300:]}")
    
    try:
        response2 = await evaluator.generate_response(context_text, max_tokens=1000)
        print(f"✅ Second prompt with context worked: {len(response2['text'])} chars")
        print(f"Response preview: {response2['text'][:200]}...")
    except Exception as e:
        print(f"❌ Second prompt with context failed: {e}")
    
    # Test 4: Second prompt without context (isolated)
    print(f"\n🧪 Test 4: Second prompt isolated (no context)")
    try:
        response3 = await evaluator.generate_response(second_prompt, max_tokens=1000)
        print(f"✅ Second prompt isolated worked: {len(response3['text'])} chars") 
        print(f"Response preview: {response3['text'][:200]}...")
    except Exception as e:
        print(f"❌ Second prompt isolated failed: {e}")
    
    # Test 5: Test with shorter context
    print(f"\n🧪 Test 5: Second prompt with truncated context")
    short_context = first_response_text[-1000:] + "\n\n" + second_prompt  # Only last 1000 chars
    print(f"Truncated context length: {len(short_context)} chars")
    
    try:
        response4 = await evaluator.generate_response(short_context, max_tokens=1000)
        print(f"✅ Second prompt with short context worked: {len(response4['text'])} chars")
        print(f"Response preview: {response4['text'][:200]}...")
    except Exception as e:
        print(f"❌ Second prompt with short context failed: {e}")
    
    await evaluator.cleanup()
    print("\n🏁 Debug complete")

if __name__ == "__main__":
    asyncio.run(debug_context_issue())
