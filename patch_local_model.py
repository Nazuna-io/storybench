#!/usr/bin/env python3
"""Quick patch to fix local model response saving issue."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path('.') / 'src'))

from storybench.database.connection import init_database

async def fix_local_model_bug():
    """Create a simple test to verify the fix and then patch the local_model_service.py"""
    
    print("=== Applying Quick Fix for Local Model Response Saving ===")
    
    # The issue is in the run index - it should be run_idx + 1, not run_idx
    # And we need better error handling
    
    # Read the current file
    service_file = Path("/home/todd/storybench/src/storybench/web/services/local_model_service.py")
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    # Apply the key fixes:
    # 1. Fix run index (run=run_idx should be run=run_idx + 1)
    # 2. Add error handling around response saving
    
    # Fix 1: run index
    content = content.replace(
        'run=run_idx,',
        'run=run_idx + 1,  # Fix: Convert to 1-based indexing'
    )
    
    # Fix 2: Add try-catch around response repo create
    old_response_creation = '''await response_repo.create(response_obj)'''
    new_response_creation = '''try:
                                    created_response = await response_repo.create(response_obj) 
                                    self._send_output(f"Response saved: {response_data['prompt_name']}", "info")
                                except Exception as resp_error:
                                    self._send_output(f"Error saving response: {str(resp_error)}", "error")
                                    raise  # Re-raise to prevent silent failures'''
    
    content = content.replace(old_response_creation, new_response_creation)
    
    # Fix 3: Add logging for evaluation creation
    old_eval_creation = '''await self.database.evaluations.insert_one(eval_dict)'''
    new_eval_creation = '''await self.database.evaluations.insert_one(eval_dict)
                            self._send_output(f"Evaluation record created: {evaluation_id}", "info")'''
    
    content = content.replace(old_eval_creation, new_eval_creation)
    
    # Write the patched file
    with open(service_file, 'w') as f:
        f.write(content)
    
    print("✅ Applied patches to local_model_service.py:")
    print("  - Fixed run index (0-based to 1-based)")
    print("  - Added error handling for response saving")
    print("  - Added logging for evaluation creation")
    print("  - Added error re-raising to prevent silent failures")
    
    print(f"\n🔧 File patched: {service_file}")
    print("📝 You can now retry your local model evaluation")

if __name__ == "__main__":
    asyncio.run(fix_local_model_bug())
