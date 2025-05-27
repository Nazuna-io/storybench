from pymongo import MongoClient
import json
from bson import ObjectId

# MongoDB connection
client = MongoClient('mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority')
db = client.storybench

# Custom JSON encoder to handle ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Count evaluations
eval_count = db.evaluations.count_documents({})
print(f"Total evaluations: {eval_count}")

# Get recent evaluations
print("\nRecent evaluations:")
recent_evals = list(db.evaluations.find().sort("_id", -1).limit(3))
for eval_doc in recent_evals:
    print(f"ID: {eval_doc.get('_id')}")
    print(f"Status: {eval_doc.get('status')}")
    print(f"Models: {eval_doc.get('models', [])}")
    print(f"Created: {eval_doc.get('created_at')}")
    print("---")

# Check for local model evaluations
print("\nLocal model evaluations:")
local_evals = list(db.evaluations.find({"models": {"$regex": "local"}}).sort("_id", -1))
for eval_doc in local_evals:
    print(f"ID: {eval_doc.get('_id')}")
    print(f"Status: {eval_doc.get('status')}")
    print(f"Models: {eval_doc.get('models', [])}")
    print(f"Created: {eval_doc.get('created_at')}")
    print("---")

# Check responses collection
response_count = db.responses.count_documents({})
print(f"\nTotal responses: {response_count}")

# Get recent responses
print("\nRecent responses:")
recent_responses = list(db.responses.find().sort("_id", -1).limit(3))
for resp in recent_responses:
    print(f"ID: {resp.get('_id')}")
    print(f"Evaluation ID: {resp.get('evaluation_id')}")
    print(f"Model: {resp.get('model')}")
    print(f"Created: {resp.get('created_at')}")
    print("---")
