import os
from pymongo import MongoClient
from pprint import pprint
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = "storybench"
COLLECTION_NAME = "responses"

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in environment variables. Please check your .env file.")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

print("Sampling 5 documents from storybench.responses to inspect schema...\n")
for doc in collection.find().limit(5):
    pprint(doc)
    print("\n" + "-"*80 + "\n")

client.close()
print("Done.")
