#!/usr/bin/env python3
"""Test script for Phase 4 data migration."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
# Adjust path to go up one level from 'tests' then into 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dotenv import load_dotenv

async def test_migration():
    """Test the Phase 4 migration functionality."""
    
    print("🧪 Testing Phase 4 Migration...")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Connect to database (will use test database from .env)
        print("📡 Connecting to database...")
        from storybench.database.connection import init_database
        database = await init_database()
        
        from storybench.database.migrations.import_existing import ExistingDataImporter
        importer = ExistingDataImporter(database)
        
        # Test import
        print("📥 Testing data import...")
        output_dir = "./output"
        
        if not Path(output_dir).exists():
            print(f"❌ Output directory {output_dir} does not exist")
            return False
            
        # Run import
        stats = await importer.import_from_output_directory(output_dir)
        
        print(f"📊 Import Results:")
        print(f"  • Files processed: {stats['files_processed']}")
        print(f"  • Evaluations imported: {stats['evaluations_imported']}")
        print(f"  • Responses imported: {stats['responses_imported']}")
        print(f"  • Errors: {stats['errors']}")
        
        if stats['errors'] > 0:
            print("❌ Import had errors")
            return False
            
        # Test validation
        print("\n🔍 Testing data validation...")
        validation = await importer.validate_import_integrity()
        
        print(f"📈 Validation Results:")
        print(f"  • Total evaluations: {validation['total_evaluations']}")
        print(f"  • Total responses: {validation['total_responses']}")
        print(f"  • Orphaned responses: {validation['orphaned_responses']}")
        print(f"  • Missing fields: {len(validation['missing_required_fields'])}")
        print(f"  • Timestamp anomalies: {len(validation['timestamp_anomalies'])}")
        print(f"  • Valid: {validation['is_valid']}")
        
        if not validation['is_valid']:
            print("⚠️ Validation issues found:")
            for issue in validation['missing_required_fields'][:5]:  # Show first 5
                print(f"    • {issue}")
            for anomaly in validation['timestamp_anomalies'][:5]:  # Show first 5
                print(f"    • {anomaly}")
        
        # Test export functionality
        print("\n📤 Testing export functionality...")
        export_dir = "./test_export"
        export_path = await importer.export_for_analysis(export_dir)
        
        exported_files = list(Path(export_path).glob("*.json"))
        print(f"  • Exported {len(exported_files)} files to {export_path}")
        
        # Verify exported files match original structure
        if exported_files:
            sample_file = exported_files[0]
            print(f"  • Sample export: {sample_file.name}")
            
            import json
            with open(sample_file, 'r') as f:
                data = json.load(f)
                
            print(f"  • Contains metadata: {'metadata' in data}")
            print(f"  • Contains sequences: {'sequences' in data}")
            
            if 'metadata' in data:
                metadata = data['metadata']
                print(f"    - Model: {metadata.get('model_name', 'unknown')}")
                print(f"    - Timestamp: {metadata.get('timestamp', 'unknown')}")
                
        print("\n✅ Phase 4 migration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_test_data():
    """Clean up test data from database."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        load_dotenv()
        from storybench.database.connection import init_database
        database = await init_database()
        
        # Remove test collections
        await database.evaluations.delete_many({})
        await database.responses.delete_many({})
        await database.evaluation_scores.delete_many({})
        
        print("✅ Test data cleaned up")
        
        # Remove test export directory
        import shutil
        test_export = Path("./test_export")
        if test_export.exists():
            shutil.rmtree(test_export)
            print("✅ Test export directory removed")
            
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    async def main():
        success = await test_migration()
        
        if success:
            print("\n🎉 All tests passed!")
            
            # Ask if user wants to keep test data
            response = input("\nKeep test data in database? (y/N): ").lower().strip()
            if response != 'y':
                await cleanup_test_data()
        else:
            print("\n💥 Tests failed!")
            await cleanup_test_data()
            sys.exit(1)
    
    asyncio.run(main())
