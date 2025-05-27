#!/usr/bin/env python3
"""Upload complete prompts configuration to database."""

import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

from src.storybench.database.connection import init_database
from src.storybench.database.services.config_service import ConfigService


async def upload_prompts():
    """Upload the complete prompts configuration from config file."""
    
    # Load prompts from config file
    with open('config/prompts.json', 'r') as f:
        prompts_data = json.load(f)
    
    print(f"Found {len(prompts_data)} sequences:")
    for seq_name, prompts in prompts_data.items():
        print(f"  {seq_name}: {len(prompts)} prompts")
    
    # Initialize database and config service
    database = await init_database()
    config_service = ConfigService(database)
    
    # Format for the config service
    config_data = {"sequences": prompts_data}
    
    try:
        # Save the configuration
        result = await config_service.save_prompts_config(config_data)
        print(f"✅ Successfully uploaded prompts configuration")
        print(f"   Config hash: {result.config_hash}")
        print(f"   Version: {result.version}")
        print(f"   Sequences: {list(result.sequences.keys())}")
        
    except Exception as e:
        print(f"❌ Failed to upload prompts: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(upload_prompts())
