#!/usr/bin/env python3
"""
Test the exact Directus evaluation query that's failing.
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


async def test_evaluation_query():
    """Test the exact query that's being used."""
    
    print("🎯 TESTING EXACT DIRECTUS EVALUATION QUERY")
    print("="*50)
    
    directus_client = DirectusClient(
        base_url=os.getenv('DIRECTUS_URL'),
        token=os.getenv('DIRECTUS_TOKEN')
    )
    
    try:
        # Test the basic query first
        print("🔍 STEP 1: BASIC PUBLISHED QUERY")
        print("-" * 30)
        
        basic_params = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'limit': '1'
        }
        
        basic_response = await directus_client._make_request('GET', '/items/evaluation_versions', params=basic_params)
        print(f"✅ Basic query successful: {len(basic_response.get('data', []))} items")
        
        if basic_response.get('data'):
            item = basic_response['data'][0]
            print(f"   Found: v{item.get('version_number')} '{item.get('version_name')}'")
            print(f"   Available fields: {list(item.keys())}")
        
        # Test with the full fields parameter that's causing issues
        print(f"\n🔍 STEP 2: FULL QUERY WITH JUNCTION FIELDS")
        print("-" * 40)
        
        full_params = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'limit': '1',
            'fields': '*,evaluation_criteria_in_version.evaluation_criteria_id.*,scoring_in_version.scoring_id.*'
        }
        
        try:
            full_response = await directus_client._make_request('GET', '/items/evaluation_versions', params=full_params)
            print(f"✅ Full query successful: {len(full_response.get('data', []))} items")
            
            if full_response.get('data'):
                item = full_response['data'][0]
                print(f"   Found: v{item.get('version_number')} '{item.get('version_name')}'")
                print(f"   Available fields: {list(item.keys())}")
                
                # Check junction table fields
                criteria_field = item.get('evaluation_criteria_in_version')
                scoring_field = item.get('scoring_in_version')
                
                print(f"   evaluation_criteria_in_version: {type(criteria_field)} - {criteria_field}")
                print(f"   scoring_in_version: {type(scoring_field)} - {scoring_field}")
            
        except Exception as e:
            print(f"❌ Full query failed: {e}")
            print("   The junction tables might not exist or have different names")
        
        # Test simplified fields
        print(f"\n🔍 STEP 3: SIMPLIFIED FIELDS QUERY")
        print("-" * 35)
        
        simple_params = {
            'filter[status][_eq]': 'published',
            'sort': '-version_number',
            'limit': '1',
            'fields': '*'
        }
        
        simple_response = await directus_client._make_request('GET', '/items/evaluation_versions', params=simple_params)
        print(f"✅ Simplified query successful: {len(simple_response.get('data', []))} items")
        
        if simple_response.get('data'):
            item = simple_response['data'][0]
            print(f"   Fields available: {list(item.keys())}")
        
        # Test what other evaluation collections exist
        print(f"\n🔍 STEP 4: CHECK OTHER EVALUATION COLLECTIONS")
        print("-" * 45)
        
        collections_to_test = [
            'evaluation_criteria',
            'evaluation_criteria_in_version',
            'scoring',
            'scoring_in_version'
        ]
        
        for collection in collections_to_test:
            try:
                test_response = await directus_client._make_request('GET', f'/items/{collection}', params={'limit': '1'})
                items = test_response.get('data', [])
                print(f"   {collection}: {len(items)} items exist")
                
            except Exception as e:
                print(f"   {collection}: ❌ Error - {e}")
        
        print(f"\n✅ QUERY TESTING COMPLETE")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_evaluation_query())
