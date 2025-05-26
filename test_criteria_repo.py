#!/usr/bin/env python3
"""Test the criteria repository to see why find_active() is failing."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, '/home/todd/storybench/src')

async def test_criteria_repo():
    load_dotenv()
    
    from storybench.database.connection import DatabaseConnection
    from storybench.database.repositories.criteria_repo import CriteriaRepository
    
    try:
        # Connect to database
        db_conn = DatabaseConnection()
        await db_conn.connect(os.getenv('MONGODB_URI'))
        
        # Test the repository
        criteria_repo = CriteriaRepository(db_conn.db)
        
        print('🔍 TESTING CRITERIA REPOSITORY\n')
        
        # Test find_active method
        active_criteria = await criteria_repo.find_active()
        
        print(f'find_active() result: {active_criteria}')
        
        if active_criteria:
            print(f'   Version: {active_criteria.version}')
            print(f'   Has criteria: {hasattr(active_criteria, "criteria")}')
            if hasattr(active_criteria, 'criteria'):
                print(f'   Criteria count: {len(active_criteria.criteria) if active_criteria.criteria else 0}')
        else:
            print('   ❌ No active criteria found!')
            
            # Debug: check raw database query
            raw_result = await db_conn.db.evaluation_criteria.find_one({"is_active": True})
            print(f'   Raw DB query result: {"Found" if raw_result else "Not found"}')
            
            if raw_result:
                print(f'   Raw ID: {raw_result.get("_id")}')
                print(f'   Raw is_active: {raw_result.get("is_active")}')
                print(f'   Raw version: {raw_result.get("version")}')
                
                # Try to understand why the repository isn't working
                print('\n🔍 Repository investigation:')
                all_results = await criteria_repo.find_many({"is_active": True})
                print(f'   find_many with is_active=True: {len(all_results)} results')
        
        await db_conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_criteria_repo())
