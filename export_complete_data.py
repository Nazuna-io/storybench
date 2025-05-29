#!/usr/bin/env python3
"""
Direct MongoDB Export for Storybench Report Generation

This script directly queries MongoDB to export evaluation data
in the format expected by the report generators.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

async def export_evaluation_data():
    """Export evaluation data directly from MongoDB."""
    
    try:
        # Try to import without the problematic unified_context_system
        sys.path.insert(0, '/home/todd/storybench/src')
        
        from storybench.database.connection import get_database
        from bson import ObjectId
        
        print("🔗 Connecting to MongoDB...")
        
        # Load environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        from storybench.database.connection import init_database
        db = await init_database()
        
        # Get collections (correct collection names!)
        responses_collection = db['responses']
        evaluations_collection = db['response_llm_evaluations']  # Fixed: was looking at wrong collection!
        
        print("📊 Exporting responses...")
        responses = []
        async for response in responses_collection.find():
            # Convert ObjectId to string for JSON serialization
            response['_id'] = str(response['_id'])
            if 'evaluation_id' in response and isinstance(response['evaluation_id'], ObjectId):
                response['evaluation_id'] = str(response['evaluation_id'])
            responses.append(response)
        
        print(f"✓ Found {len(responses)} responses")
        
        print("📝 Exporting evaluations...")
        evaluations = []
        async for evaluation in evaluations_collection.find():
            # Convert ObjectId to string
            evaluation['_id'] = str(evaluation['_id'])
            if 'response_id' in evaluation and isinstance(evaluation['response_id'], ObjectId):
                evaluation['response_id'] = str(evaluation['response_id'])
            evaluations.append(evaluation)
        
        print(f"✓ Found {len(evaluations)} evaluations")
        
        # Create export data structure
        export_data = {
            "status": "success",
            "test_type": "mongodb_export",
            "export_timestamp": datetime.now().isoformat(),
            "total_responses": len(responses),
            "total_evaluations": len(evaluations),
            "responses": responses,
            "evaluations": evaluations
        }
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"complete_storybench_data_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Complete data exported to: {output_file}")
        print(f"📊 Summary:")
        print(f"   - Responses: {len(responses)}")
        print(f"   - Evaluations: {len(evaluations)}")
        
        # Show model breakdown
        models = {}
        for response in responses:
            model = response.get('model_name', 'unknown')
            models[model] = models.get(model, 0) + 1
        
        print(f"   - Models: {len(models)}")
        for model, count in sorted(models.items(), key=lambda x: x[1], reverse=True):
            print(f"     • {model}: {count} responses")
        
        return output_file
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing missing dependencies or running from virtual environment")
        return None
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return None

if __name__ == "__main__":
    file_path = asyncio.run(export_evaluation_data())
    if file_path:
        print(f"\n🚀 Next steps:")
        print(f"   python3 simple_report_generator.py {file_path} enhanced_report.md")
        print(f"   python3 run_report.py --data {file_path}")
