#!/usr/bin/env python3
"""
Test script to verify API connections and evaluator creation.
"""
import asyncio
import os
import sys
sys.path.append('/home/todd/storybench/src')

from storybench.evaluators.factory import EvaluatorFactory
from storybench.database.connection import init_database, get_database
from storybench.database.repositories.model_repo import ModelRepository

async def test_api_connections():
    """Test API connections for all configured models."""
    
    print("🔍 Testing API Connections...")
    print("=" * 60)
    
    try:
        # Initialize database connection
        await init_database()
        database = await get_database()
        model_repo = ModelRepository(database)
        
        # Get all models
        models_configs = await model_repo.find_many({})
        print(f"📊 Found {len(models_configs)} model configurations")
        
        # Get individual models from all configurations
        all_models = []
        for config in models_configs:
            all_models.extend(config.models)
        
        print(f"🤖 Total individual models: {len(all_models)}")
        
        # Filter for ChatGPT models
        chatgpt_models = [m for m in all_models if any(pattern in m.name.lower() for pattern in ['gpt', 'o3', 'o1'])]
        print(f"🤖 ChatGPT models: {len(chatgpt_models)}")
        
        for model in chatgpt_models:
            print(f"\n📝 Testing model: {model.name}")
            print(f"  Type: {model.type}")
            print(f"  Provider: {model.provider}")
            print(f"  Model Name: {model.model_name}")
            
            try:
                # Get API keys
                api_keys = {
                    "openai": os.getenv("OPENAI_API_KEY"),
                    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
                    "google": os.getenv("GOOGLE_API_KEY")
                }
                
                # Create model config dict for evaluator factory
                model_config = {
                    "type": model.type.value if hasattr(model.type, 'value') else str(model.type),
                    "provider": model.provider,
                    "model_name": model.model_name,
                    "repo_id": model.repo_id,
                    "filename": model.filename,
                    "subdirectory": model.subdirectory
                }
                
                # Create evaluator
                evaluator = EvaluatorFactory.create_evaluator(
                    model.name,
                    model_config,
                    api_keys
                )
                
                print(f"  ✅ Evaluator created successfully")
                
                # Setup evaluator
                setup_success = await evaluator.setup()
                if not setup_success:
                    print(f"  ❌ Evaluator setup failed")
                    continue
                
                print(f"  ✅ Evaluator setup successful")
                
                # Test a simple API call
                test_prompt = "Write a single sentence about a cat."
                print(f"  🧪 Testing API call...")
                
                response = await evaluator.generate_response(test_prompt)
                print(f"  ✅ API call successful")
                print(f"  📝 Response: {response.get('response', '')[:100]}...")
                
                # Cleanup
                await evaluator.cleanup()
                print(f"  🧹 Cleanup successful")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n" + "=" * 60)
        print("✅ API connection test complete!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_connections())
