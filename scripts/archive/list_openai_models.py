#!/usr/bin/env python3
"""
Script to list all available OpenAI models and API version information.
"""
import os
import asyncio
from openai import AsyncOpenAI

async def list_openai_models():
    """List all available OpenAI models and API information."""
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not found!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)
        
        print("🔍 Fetching OpenAI models and API information...")
        print("=" * 60)
        
        # Get all available models
        models_response = await client.models.list()
        models = sorted(models_response.data, key=lambda x: x.id)
        
        print(f"📊 Total Models Available: {len(models)}")
        print("=" * 60)
        
        # Categorize models
        gpt_models = []
        embedding_models = []
        other_models = []
        
        for model in models:
            model_id = model.id
            if "gpt" in model_id.lower():
                gpt_models.append(model)
            elif "embedding" in model_id.lower() or "ada" in model_id.lower():
                embedding_models.append(model)
            else:
                other_models.append(model)
        
        # Display GPT models
        print(f"\n🤖 GPT Models ({len(gpt_models)}):")
        print("-" * 40)
        for model in gpt_models:
            print(f"  • {model.id}")
            if hasattr(model, 'created'):
                from datetime import datetime
                created_date = datetime.fromtimestamp(model.created).strftime('%Y-%m-%d')
                print(f"    Created: {created_date}")
            if hasattr(model, 'owned_by'):
                print(f"    Owner: {model.owned_by}")
            print()
        
        # Display embedding models
        print(f"\n🔗 Embedding Models ({len(embedding_models)}):")
        print("-" * 40)
        for model in embedding_models:
            print(f"  • {model.id}")
            if hasattr(model, 'owned_by'):
                print(f"    Owner: {model.owned_by}")
            print()
        
        # Display other models
        if other_models:
            print(f"\n🔧 Other Models ({len(other_models)}):")
            print("-" * 40)
            for model in other_models:
                print(f"  • {model.id}")
                if hasattr(model, 'owned_by'):
                    print(f"    Owner: {model.owned_by}")
                print()
        
        # Test API with a simple request to get more version info
        print("\n🔍 Testing API Connection...")
        print("-" * 40)
        
        try:
            # Make a simple completion request to test the API
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "What is the current OpenAI API version?"}],
                max_tokens=100
            )
            
            print("✅ API Connection: Successful")
            print(f"📝 Test Response: {response.choices[0].message.content[:100]}...")
            
            # Check response headers for version info if available
            if hasattr(response, 'headers'):
                print(f"🔢 Response Headers: {response.headers}")
            
        except Exception as e:
            print(f"⚠️  API Test Warning: {e}")
        
        # Display client version
        try:
            import openai
            print(f"\n📦 OpenAI Python Library Version: {openai.__version__}")
        except:
            print("\n📦 OpenAI Python Library Version: Unknown")
        
        print("\n" + "=" * 60)
        print("✅ Model listing complete!")
        
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        print("Please check your API key and internet connection.")

if __name__ == "__main__":
    asyncio.run(list_openai_models())
