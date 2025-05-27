#!/usr/bin/env python3
"""Test full local model evaluation with SSE and database."""

import asyncio
import aiohttp
import json

async def test_full_evaluation():
    """Test full evaluation with database storage."""
    print("Testing full local model evaluation...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Start evaluation with database storage
            print("1. Starting evaluation with database storage...")
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
                    "max_tokens": 100,
                    "num_runs": 1,
                    "vram_limit_percent": 80,
                    "auto_evaluate": False  # Skip API evaluation for this test
                }
            }
            
            # Start evaluation
            async def start_evaluation():
                await asyncio.sleep(1)  # Wait for SSE connection
                async with session.post('http://localhost:8000/api/local-models/start', json=eval_payload) as resp:
                    result = await resp.json()
                    print(f"Evaluation started: {result}")
            
            # Listen to SSE events
            print("2. Listening to console output...")
            async with session.get('http://localhost:8000/api/local-models/events') as resp:
                # Start evaluation after connecting to SSE
                asyncio.create_task(start_evaluation())
                
                console_messages = []
                event_count = 0
                
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line and line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            event_count += 1
                            
                            if 'console_type' in data:
                                console_msg = f"[{data['console_type']}] {data['message']}"
                                console_messages.append(console_msg)
                                print(console_msg)
                            elif 'status' in data:
                                print(f"[STATUS] {data['status']} - Progress: {data.get('progress', 0)}%")
                                
                                if data['status'] in ['completed', 'failed']:
                                    print("Evaluation finished!")
                                    break
                        except json.JSONDecodeError:
                            pass
                        
                        # Safety exit
                        if event_count > 50:
                            print("Max events reached, stopping...")
                            break
                
                print(f"\n3. Captured {len(console_messages)} console messages:")
                for msg in console_messages:
                    print(f"  {msg}")
                    
    except Exception as e:
        print(f"Error testing full evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_evaluation())
