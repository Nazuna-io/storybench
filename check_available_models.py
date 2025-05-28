#!/usr/bin/env python3
"""
Check available model configurations for end-to-end testing.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.database.connection import get_database, init_database


async def check_available_models():
    """Check what model configurations are available in the database."""
    print("🔍 CHECKING AVAILABLE MODEL CONFIGURATIONS")
    print("="*60)
    
    try:
        # Initialize and get database connection
        await init_database()
        database = await get_database()
        
        # Check model configurations
        print("📋 Model Configurations:")
        configs = list(database.model_configs.find())
        
        if not configs:
            print("   ❌ No model configurations found")
            return []
        
        for config in configs:
            print(f"\n   Configuration ID: {config['_id']}")
            print(f"   Name: {config.get('name', 'Unnamed')}")
            print(f"   Active: {config.get('active', False)}")
            print(f"   Created: {config.get('created_at', 'Unknown')}")
            
            models = config.get('models', [])
            print(f"   Models ({len(models)}):")
            
            for model in models:
                model_type = model.get('provider', 'unknown')
                model_name = model.get('name', 'unnamed')
                model_path = model.get('model', 'no-path')
                
                if model_type == 'local':
                    print(f"     🖥️  {model_name} (LOCAL: {model_path})")
                else:
                    print(f"     🌐 {model_name} ({model_type}: {model_path})")
        
        # Check for any local model specific configurations
        print("\n📋 Local Model Service Status:")
        local_models_collection = database.local_models
        local_models = list(local_models_collection.find())
        
        if local_models:
            for local_model in local_models:
                print(f"   Local Model: {local_model}")
        else:
            print("   No local model specific configurations found")
        
        # Check current responses to see what models have been used
        print("\n📊 Recent Response History (last 10):")
        recent_responses = list(database.responses.find().sort("_id", -1).limit(10))
        
        if recent_responses:
            used_models = set()
            for response in recent_responses:
                model_name = response.get('model_name', 'unknown')
                used_models.add(model_name)
            
            print("   Models that have generated responses:")
            for model in sorted(used_models):
                count = database.responses.count_documents({"model_name": model})
                print(f"     📝 {model}: {count} responses")
        else:
            print("   No responses found in database")
            
        return configs
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """Main function."""
    configs = await check_available_models()
    
    print("\n" + "="*60)
    if configs:
        print("✅ Model configurations found - ready for end-to-end testing")
    else:
        print("❌ No model configurations found")
        print("   You may need to configure models in the web interface first")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
