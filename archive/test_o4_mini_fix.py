#!/usr/bin/env python3
"""Quick test for o4-mini specifically to verify the fix"""

import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))
from storybench.evaluators.api_evaluator import APIEvaluator

async def test_o4_mini():
    """Test o4-mini specifically with correct parameters."""
    print("Testing o4-mini with max_completion_tokens...")
    
    api_keys = {"openai": os.getenv("OPENAI_API_KEY")}
    
    model_config = {
        "provider": "openai",
        "model_name": "o4-mini",
        "temperature": 0.5,
        "max_completion_tokens": 50  # Use max_completion_tokens for o4-mini
    }
    
    evaluator = APIEvaluator("test-o4-mini", model_config, api_keys)
    
    try:
        setup_success = await evaluator.setup()
        print(f"Setup: {'✅ Success' if setup_success else '❌ Failed'}")
        
        if setup_success:
            # Test generation with max_completion_tokens parameter
            result = await evaluator.generate_response(
                prompt="Say hello in one word",
                temperature=0.3,
                max_completion_tokens=10
            )
            
            if result and "response" in result:
                print(f"✅ Generation successful: '{result['response'][:50]}...'")
                print(f"   Time: {result.get('generation_time', 0):.2f}s")
                return True
            else:
                print("❌ No response generated")
                return False
        else:
            print("❌ Setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await evaluator.cleanup()

if __name__ == "__main__":
    success = asyncio.run(test_o4_mini())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
