#!/usr/bin/env python3
"""
Debug Directus Evaluation Collections

This script checks what evaluation-related collections exist in Directus
and what data is available.
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.clients.directus_client import DirectusClient


async def debug_directus_evaluation_collections():
    """Debug what's available in Directus for evaluation collections."""
    
    print("🔍 DEBUGGING DIRECTUS EVALUATION COLLECTIONS")
    print("="*60)
    
    directus_client = DirectusClient(
        base_url=os.getenv('DIRECTUS_URL'),
        token=os.getenv('DIRECTUS_TOKEN')
    )
    
    try:
        # Check what collections exist
        print("📚 STEP 1: CHECKING AVAILABLE COLLECTIONS")
        print("-" * 50)
        
        collections_response = await directus_client._make_request('GET', '/collections')
        collections = [c['collection'] for c in collections_response.get('data', [])]
        
        evaluation_related = [c for c in collections if 'evaluat' in c.lower()]
        
        print(f"   Total collections: {len(collections)}")
        print(f"   Evaluation-related collections: {evaluation_related}")
        
        # Check each evaluation collection
        for collection_name in evaluation_related:
            print(f"\n📊 COLLECTION: {collection_name}")
            print("-" * 30)
            
            try:
                # Get items from this collection
                items_response = await directus_client._make_request('GET', f'/items/{collection_name}')
                items = items_response.get('data', [])
                
                print(f"   Items count: {len(items)}")
                
                if items:
                    print(f"   Sample item fields: {list(items[0].keys())}")
                    
                    # If this is evaluation_versions, show details
                    if collection_name == 'evaluation_versions':
                        print(f"   Evaluation versions:")
                        for item in items:
                            status = item.get('status', 'unknown')
                            version = item.get('version_number', 'unknown')
                            name = item.get('version_name', 'unknown')
                            print(f"      - v{version}: {name} (status: {status})")
                
            except Exception as e:
                print(f"   ❌ Error accessing {collection_name}: {e}")
        
        # Test the specific query used by the code
        print(f"\n🎯 STEP 2: TESTING SPECIFIC EVALUATION VERSION QUERY")
        print("-" * 50)
        
        params = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'limit': '1',
            'fields': '*,evaluation_criteria_in_version.evaluation_criteria_id.*,scoring_in_version.scoring_id.*'
        }
        
        try:
            response_data = await directus_client._make_request('GET', '/items/evaluation_versions', params=params)
            
            if response_data.get('data'):
                print(f"   ✅ Found {len(response_data['data'])} published evaluation version(s)")
                for item in response_data['data']:
                    print(f"      - v{item.get('version_number')}: {item.get('version_name')} (status: {item.get('status')})")
            else:
                print(f"   ❌ No published evaluation versions found")
                print(f"   Raw response: {json.dumps(response_data, indent=2)}")
        
        except Exception as e:
            print(f"   ❌ Error with evaluation version query: {e}")
        
        # Check if evaluation_versions collection exists and what's in it
        print(f"\n📝 STEP 3: RAW EVALUATION_VERSIONS DATA")
        print("-" * 50)
        
        try:
            all_versions_response = await directus_client._make_request('GET', '/items/evaluation_versions')
            all_versions = all_versions_response.get('data', [])
            
            print(f"   Total evaluation versions: {len(all_versions)}")
            
            for version in all_versions:
                version_num = version.get('version_number', 'N/A')
                name = version.get('version_name', 'N/A')
                status = version.get('status', 'N/A')
                print(f"      v{version_num}: {name} (status: {status})")
        
        except Exception as e:
            print(f"   ❌ Error getting all evaluation versions: {e}")
        
        print(f"\n✅ DEBUGGING COMPLETE")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")


if __name__ == "__main__":
    asyncio.run(debug_directus_evaluation_collections())
