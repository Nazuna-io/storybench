from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get("MONGODB_URI")
if not uri:
    print("No MONGODB_URI set!")
    exit(1)

client = MongoClient(uri)
db_name = uri.split('/')[-1].split('?')[0] if 'mongodb+srv' not in uri else 'storybench'
db = client[db_name]

def print_latest_evaluations():
    print("\n=== Latest Evaluations ===")
    for ev in db.evaluations.find({}).sort("created_at", -1).limit(3):
        print(f"ID: {ev.get('_id')} | status: {ev.get('status')} | created: {ev.get('created_at')} | models: {ev.get('models')} | total_tasks: {ev.get('total_tasks')} | completed_tasks: {ev.get('completed_tasks')}")

def print_latest_responses():
    print("\n=== Latest Responses ===")
    for resp in db.responses.find({}).sort("created_at", -1).limit(3):
        print(f"ID: {resp.get('_id')} | evaluation_id: {resp.get('evaluation_id')} | model: {resp.get('model_name')} | created: {resp.get('created_at')}")

if __name__ == "__main__":
    print_latest_evaluations()
    print_latest_responses()
