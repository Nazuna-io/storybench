#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
import hashlib
import json

load_dotenv()

async def create_prompts_config():
    """Create prompts configuration directly in database."""
    
    mongodb_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.storybench
    
    try:
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Create prompts configuration matching the structure
        prompts_data = {
            "FilmNarrative": [
                {
                    "name": "Initial Concept",
                    "text": "Create a completely original feature film concept set 15-20 years in the future that explores whether objective reality exists. Include a synopsis, main characters, and setting. Your concept should feature innovative visual elements that would be distinctive on screen, avoid common sci-fi tropes (no simulations, no 'it was all a dream'), and present a genuinely new perspective on perception vs reality."
                },
                {
                    "name": "Scene Development",
                    "text": "Based on your previous concept, develop one pivotal scene with dialogue that reveals character psychology and advances the philosophical themes about the nature of reality. This scene should demonstrate the central conflict or revelation in your story."
                },
                {
                    "name": "Visual Realization", 
                    "text": "Create a detailed description of the most visually striking frame from your film concept. Describe composition, lighting, and emotional impact as if designing a storyboard frame in 16:9 aspect ratio. What specific visual techniques would be used to capture this moment, and why is this particular image central to your story?"
                }
            ]
        }
        
        # Generate config hash
        config_str = json.dumps(prompts_data, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        # Create document structure
        prompts_config = {
            "config_hash": config_hash,
            "version": 1,
            "sequences": prompts_data,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Insert into database
        result = await db.prompts.insert_one(prompts_config)
        print(f"✅ Prompts configuration created with ID: {result.inserted_id}")
        print(f"   Config Hash: {config_hash}")
        print(f"   Sequences: {list(prompts_data.keys())}")
        
        # Verify it was created
        count = await db.prompts.count_documents({"is_active": True})
        print(f"✅ Active prompts configs in database: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_prompts_config())
