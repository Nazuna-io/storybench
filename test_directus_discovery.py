#!/usr/bin/env python3
"""Test script to discover Directus collections and understand the evaluation schema."""

import asyncio
import os
import sys
import httpx
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, 'src')

from storybench.clients.directus_client import DirectusClient, DirectusClientError


async def discover_evaluation_collections():
    """Try to discover evaluation collections by attempting to access them directly."""
    try:
        client = DirectusClient()
        
        # Check basic connection
        print("Testing Directus connection...")
        connection_ok = await client.test_connection()
        print(f"Connection: {'OK' if connection_ok else 'FAILED'}")
        
        if not connection_ok:
            return
            
        print("\nLooking for evaluation-related collections...")
        
        # Try common evaluation collection patterns
        potential_names = [
            'evaluation_criteria',
            'evaluation_versions', 
            'evaluation_versions_evaluation_criteria',
            'evaluation_versions_scoring',
            'scoring',
            'evaluation_prompts',
            'scoring_guidelines',
            'evaluation_prompt_sets',
            'criterion_definitions',
            'evaluations',
            'criteria',
            'guidelines',
            'evaluation_templates',
            'eval_criteria',
            'eval_prompts',
            'llm_evaluation_criteria',
            'llm_evaluation_prompts',
            'evaluation_rubrics',
            'rubrics'
        ]
        
        found_collections = []
        
        for name in potential_names:
            try:
                # Try to get items from the collection
                items_response = await client._make_request("GET", f"/items/{name}?limit=3")
                items = items_response.get('data', [])
                
                if items:
                    found_collections.append((name, items))
                    print(f" Found collection: {name} ({len(items)} items)")
                else:
                    print(f"  Found empty collection: {name}")
                    found_collections.append((name, []))
                    
            except Exception as e:
                # Show detailed error for debugging
                print(f" Error accessing {name}: {e}")
                # Collection doesn't exist or no access
                if "does not exist" in str(e) or "FORBIDDEN" in str(e):
                    continue
                else:
                    print(f"  Unexpected error type: {type(e)}")
                    continue
        
        if found_collections:
            print(f"\n{'='*60}")
            print("DETAILED ANALYSIS OF FOUND COLLECTIONS")
            print(f"{'='*60}")
            
            for collection_name, items in found_collections:
                print(f"\n=== {collection_name.upper()} ===")
                
                if not items:
                    print("  No items in collection")
                    continue
                
                # Analyze structure of first item
                sample = items[0]
                print(f"  Structure of first item:")
                
                for key, value in sample.items():
                    if isinstance(value, str) and len(value) > 150:
                        display_value = f'"{value[:150]}..."'
                    elif isinstance(value, list) and len(value) > 3:
                        display_value = f"[{len(value)} items: {value[:3]}...]"
                    elif isinstance(value, dict):
                        display_value = f"{{dict with keys: {list(value.keys())}}}"
                    else:
                        display_value = repr(value)
                    
                    print(f"    {key}: {display_value} ({type(value).__name__})")
                
                # Show all items if there are few
                if len(items) <= 3:
                    for i, item in enumerate(items):
                        print(f"\n  Item {i+1}:")
                        for key, value in item.items():
                            if key in ['id', 'name', 'title', 'description', 'prompt', 'criteria', 'scale']:
                                if isinstance(value, str) and len(value) > 200:
                                    display_value = f'"{value[:200]}..."'
                                else:
                                    display_value = repr(value)
                                print(f"    {key}: {display_value}")
                
                print()
        else:
            print("\n No evaluation-related collections found")
            print("This might mean:")
            print("  1. Collections use different naming conventions")
            print("  2. Evaluation data is stored in different collections")  
            print("  3. Collections haven't been created yet")
            print("  4. Access permissions are limited")
                
    except DirectusClientError as e:
        print(f"Directus error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def check_existing_prompt_structure():
    """Check how existing prompts are structured to understand the pattern."""
    try:
        client = DirectusClient()
        
        print("\n" + "="*60)
        print("CHECKING EXISTING PROMPT STRUCTURE FOR REFERENCE")
        print("="*60)
        
        # Try to access existing prompt collections that we know work
        known_collections = [
            'prompt_set_versions',
            'prompt_sequences', 
            'prompts'
        ]
        
        for collection_name in known_collections:
            try:
                print(f"\n--- {collection_name} ---")
                items_response = await client._make_request("GET", f"/items/{collection_name}?limit=2")
                items = items_response.get('data', [])
                
                if items:
                    print(f"  Found {len(items)} items")
                    
                    # Show structure
                    sample = items[0]
                    print(f"  Sample structure:")
                    for key, value in sample.items():
                        if isinstance(value, str) and len(value) > 100:
                            display_value = f'"{value[:100]}..."'
                        elif isinstance(value, list):
                            display_value = f"[{len(value)} items]"
                        elif isinstance(value, dict):
                            display_value = f"{{dict with {len(value)} keys}}"
                        else:
                            display_value = repr(value)
                        print(f"    {key}: {display_value}")
                else:
                    print(f"  Empty collection")
                    
            except Exception as e:
                print(f"  Error accessing {collection_name}: {e}")
                
    except Exception as e:
        print(f"Error checking existing structure: {e}")


if __name__ == "__main__":
    print("Directus Discovery Tool")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print(f"Directus URL: {os.getenv('DIRECTUS_URL', 'Not configured')}")
    print(f"Directus Token: {'Configured' if os.getenv('DIRECTUS_TOKEN') else 'Not configured'}")
    print()
    
    asyncio.run(discover_evaluation_collections())
    asyncio.run(check_existing_prompt_structure())
