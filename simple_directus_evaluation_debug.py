#!/usr/bin/env python3
"""
Simple Directus Evaluation Debug

Directly check the evaluation_versions collection without admin permissions.
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


async def simple_evaluation_debug():
    """Simple debug of evaluation collections."""
    
    print("🔍 SIMPLE DIRECTUS EVALUATION DEBUG")
    print("="*50)
    
    directus_client = DirectusClient(
        base_url=os.getenv('DIRECTUS_URL'),
        token=os.getenv('DIRECTUS_TOKEN')
    )
    
    try:
        # Check evaluation_versions collection directly
        print("📊 CHECKING EVALUATION_VERSIONS COLLECTION")
        print("-" * 40)
        
        # First, try to get all evaluation versions
        try:
            all_response = await directus_client._make_request('GET', '/items/evaluation_versions')
            all_versions = all_response.get('data', [])
            
            print(f"✅ Total evaluation versions: {len(all_versions)}")
            
            if all_versions:
                print("   All versions found:")
                for version in all_versions:
                    v_num = version.get('version_number', 'N/A')
                    v_name = version.get('version_name', 'N/A')
                    v_status = version.get('status', 'N/A')
                    v_id = version.get('id', 'N/A')
                    print(f"      ID {v_id}: v{v_num} '{v_name}' (status: {v_status})")
            else:
                print("   ❌ No evaluation versions found")
                
        except Exception as e:
            print(f"   ❌ Error getting all evaluation versions: {e}")
        
        # Now test the specific published query
        print(f"\n🎯 TESTING PUBLISHED QUERY")
        print("-" * 30)
        
        try:
            params = {
                'filter[status][_eq]': 'published',
                'sort': '-version_number',
                'limit': '1'
            }
            
            published_response = await directus_client._make_request('GET', '/items/evaluation_versions', params=params)
            published_versions = published_response.get('data', [])
            
            print(f"Published versions found: {len(published_versions)}")
            
            if published_versions:
                for version in published_versions:
                    v_num = version.get('version_number', 'N/A')
                    v_name = version.get('version_name', 'N/A')
                    v_status = version.get('status', 'N/A')
                    print(f"   ✅ Found: v{v_num} '{v_name}' (status: {v_status})")
            else:
                print("   ❌ No published versions found")
                
        except Exception as e:
            print(f"   ❌ Error with published query: {e}")
        
        # Try different status values
        print(f"\n🔍 TESTING DIFFERENT STATUS VALUES")
        print("-" * 35)
        
        status_tests = ['published', 'draft', 'archived']
        
        for status in status_tests:
            try:
                params = {'filter[status][_eq]': status}
                response = await directus_client._make_request('GET', '/items/evaluation_versions', params=params)
                items = response.get('data', [])
                print(f"   Status '{status}': {len(items)} versions")
                
            except Exception as e:
                print(f"   Status '{status}': Error - {e}")
        
        print(f"\n✅ DEBUG COMPLETE")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")


if __name__ == "__main__":
    asyncio.run(simple_evaluation_debug())
