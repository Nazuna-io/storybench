#!/usr/bin/env python3
"""Test SSE endpoint for local models."""

import asyncio
import aiohttp
import json

async def test_sse():
    """Test the SSE endpoint."""
    print("Testing SSE endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Start a small evaluation
            print("1. Starting evaluation...")
            eval_payload = {
                "generation_model": {
                    "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                    "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                    "subdirectory": ""
                },
                "evaluation_model": {
                    "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF", 
                    "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                    "subdirectory": ""
                },
                "use_local_evaluator": False,
                "sequences": ["FilmNarrative"],
                "settings": {
                    "temperature": 1.0,
                    "max_tokens": 50,
                    "num_runs": 1,
                    "vram_limit_percent": 80,
                    "auto_evaluate": False
                }
            }
            
            # Start evaluation in background
            async def start_evaluation():
                async with session.post('http://localhost:8000/api/local-models/start', json=eval_payload) as resp:
                    result = await resp.json()
                    print(f"Evaluation started: {result}")
            
            # Listen to SSE events
            print("2. Listening to SSE events...")
            async with session.get('http://localhost:8000/api/local-models/events') as resp:
                # Start evaluation after connecting to SSE
                asyncio.create_task(start_evaluation())
                
                event_count = 0
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line:
                        print(f"SSE: {line}")
                        event_count += 1
                        
                        # Stop after 20 events to avoid infinite loop
                        if event_count > 20:
                            print("Received enough events, stopping...")
                            break
                        
                        # Check for completion
                        if "completed" in line.lower() or "failed" in line.lower():
                            print("Evaluation completed or failed, stopping...")
                            break
                            
    except Exception as e:
        print(f"Error testing SSE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sse())
