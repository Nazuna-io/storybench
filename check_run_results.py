import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Assuming models.py is in src/storybench/database/models.py
# and this script is run from the root of storybench project
import sys
sys.path.append('src')
from storybench.database.models import Response, Evaluation, ResponseLLMEvaluation, PyObjectId

load_dotenv() # Load environment variables from .env file

MONGO_DETAILS = os.getenv("MONGODB_URI", "mongodb://localhost:27017") # Default if not found
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "storybench_db") # Default if not found

async def check_db_after_run():
    print(f"Attempting to connect to MongoDB with URI: {MONGO_DETAILS}")
    print(f"Using database name: {DATABASE_NAME}")

    client = None  # Initialize client to None
    try:
        client = AsyncIOMotorClient(MONGO_DETAILS)
        print(f"  MongoDB client object initialized. Type: {type(client)}")
        # Test connection early (optional, Motor connects lazily by default)
        # await client.admin.command('ping') 
        # print("MongoDB connection successful (ping test).")
        db = client[DATABASE_NAME]
        print(f"  Attempting to list collections in '{DATABASE_NAME}'...")
        try:
            collections = await db.list_collection_names()
            print(f"  Successfully listed collections: {collections}")
        except Exception as e_list_coll:
            print(f"  Error listing collections: {e_list_coll}")

        target_model_name = "TinyLlama-Chat-Q2_K"
        target_sequence_name = "FilmNarrative"

        print(f"--- Checking Responses for {target_model_name} / {target_sequence_name} ---")
    
    # Fetch the latest 9 responses
        responses_cursor = db.responses.find({
            "model_name": target_model_name,
            "sequence": target_sequence_name
        }).sort("completed_at", -1).limit(9)
    
        responses_found = []
        async for r_doc in responses_cursor:
            responses_found.append(Response(**r_doc))

        if not responses_found:
            print("No responses found for the specified model and sequence.")
            # No early return here, finally block will close client
            pass # Explicitly do nothing else in this if block, proceed to finally

        print(f"Found {len(responses_found)} responses. Details of the latest {len(responses_found)} (sorted newest first):")
        response_ids = []
        evaluation_ids_from_responses = set()

        for i, r in enumerate(responses_found):
            print(f"  Response {i+1}: ID: {r.id}")
            print(f"    Model: {r.model_name}, Sequence: {r.sequence}, Run: {r.run}, Prompt Index: {r.prompt_index}")
            print(f"    Prompt Name: {r.prompt_name}")
            snippet = r.response[:80].replace('\n', ' ')
            print(f"    Response Text Snippet: {snippet}...")
            print(f"    Completed At: {r.completed_at}")
            print(f"    Stored Evaluation ID: {r.evaluation_id}")
            response_ids.append(r.id)
            if r.evaluation_id and r.evaluation_id != "": # Check if not None or empty
                evaluation_ids_from_responses.add(r.evaluation_id)

        if not evaluation_ids_from_responses:
            print("\nNo valid (non-empty) evaluation_ids found in the recent responses.")
        else:
            print(f"\n--- Checking Evaluation Documents for Evaluation Job IDs: {evaluation_ids_from_responses} ---")
            for eval_id_str in evaluation_ids_from_responses:
                try:
                    eval_object_id = PyObjectId(eval_id_str) # PyObjectId can validate/convert string to ObjectId
                    evaluation_doc = await db.evaluations.find_one({"_id": eval_object_id})
                    if evaluation_doc:
                        eval_obj = Evaluation(**evaluation_doc)
                        print(f"  Found Evaluation Document for ID {eval_id_str}:")
                        print(f"    Status: {eval_obj.status}, Models: {eval_obj.models}")
                        print(f"    Total Tasks: {eval_obj.total_tasks}, Completed: {eval_obj.completed_tasks}")
                        print(f"    Error: {eval_obj.error_message}")
                    else:
                        print(f"  No Evaluation Document found for ID {eval_id_str}")
                except Exception as e:
                    print(f"  Error converting or querying for Evaluation ID {eval_id_str}: {e}")

        print("\n--- Checking for LLM-based Evaluations of these Responses ---")
        llm_evals_found_count = 0
        if response_ids:
            for resp_id in response_ids:
                llm_evals_cursor = db.response_llm_evaluations.find({"response_id": resp_id})
                async for llm_eval_doc in llm_evals_cursor:
                    llm_evals_found_count += 1
                    llm_eval_obj = ResponseLLMEvaluation(**llm_eval_doc)
                    print(f"  Found LLM Evaluation for Response ID {resp_id}: Evaluator: {llm_eval_obj.evaluating_llm_model}")
    
        if llm_evals_found_count == 0:
            print("No LLM-based evaluations found for these specific responses.")
        else:
            print(f"Total LLM-based evaluations found for these responses: {llm_evals_found_count}")

    except Exception as e:
        print(f"An error occurred during database operations: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            print(f"In finally block. Client object type before close: {type(client)}")
            print("Closing MongoDB client connection.")
            await client.close()
        else:
            print("MongoDB client was not initialized, no connection to close.")

if __name__ == "__main__":
    asyncio.run(check_db_after_run())
