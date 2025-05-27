#!/usr/bin/env python3
"""
Script to check existing responses in the database and create evaluation criteria.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.storybench.database.repositories.response_repo import ResponseRepository
from src.storybench.database.repositories.criteria_repo import CriteriaRepository
from src.storybench.database.models import EvaluationCriteria, EvaluationCriterionItem
from src.storybench.database.services.config_service import ConfigService

async def main():
    # Load environment variables
    load_dotenv()
    
    # Connect to database
    connection_string = os.getenv("MONGODB_URI")
    if not connection_string:
        print("MONGODB_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(connection_string)
    database = client["storybench"]
    
    # Initialize repositories
    response_repo = ResponseRepository(database)
    criteria_repo = CriteriaRepository(database)
    config_service = ConfigService(database)
    
    print("=== Checking Responses in Database ===")
    
    # Get all responses
    responses = await response_repo.find_many({})
    print(f"Found {len(responses)} responses in database")
    
    if responses:
        print("\nFirst few responses:")
        for i, response in enumerate(responses[:3]):
            print(f"  {i+1}. Model: {response.model_name}, Sequence: {response.sequence}, Run: {response.run}")
            print(f"     Prompt: {response.prompt_name}")
            print(f"     Response length: {len(response.response)} chars")
            print(f"     Completed: {response.completed_at}")
            print()
    
    print("=== Checking Evaluation Criteria ===")
    
    # Check existing criteria
    existing_criteria = await criteria_repo.find_many({})
    print(f"Found {len(existing_criteria)} criteria configurations")
    
    if not existing_criteria:
        print("No evaluation criteria found. Creating from eval-criteria.txt...")
        
        # Read criteria from file
        criteria_file = Path("/home/todd/eval-criteria.txt")
        if criteria_file.exists():
            criteria_text = criteria_file.read_text()
            
            # Parse the criteria (simplified for now)
            criteria_dict = {
                "creativity": {
                    "name": "creativity",
                    "description": "Originality, avoidance of tropes, innovative perspectives",
                    "scale": 5
                },
                "coherence": {
                    "name": "coherence", 
                    "description": "Consistency across the sequence, logical development of ideas",
                    "scale": 5
                },
                "character_depth": {
                    "name": "character_depth",
                    "description": "Psychological complexity, authentic motivations", 
                    "scale": 5
                },
                "dialogue_quality": {
                    "name": "dialogue_quality",
                    "description": "Naturalistic speech, character revelation through dialogue",
                    "scale": 5
                },
                "visual_imagination": {
                    "name": "visual_imagination", 
                    "description": "Distinctiveness and vividness of visual elements",
                    "scale": 5
                },
                "conceptual_depth": {
                    "name": "conceptual_depth",
                    "description": "Sophistication of themes and ideas",
                    "scale": 5
                },
                "adaptability": {
                    "name": "adaptability",
                    "description": "Success in responding to different aspects of the creative challenge", 
                    "scale": 5
                }
            }
            
            # Save criteria to database
            criteria_data = {"criteria": criteria_dict}
            saved_criteria = await config_service.save_criteria_config(criteria_data)
            print(f"Created evaluation criteria with hash: {saved_criteria.config_hash}")
        else:
            print("eval-criteria.txt file not found!")
    else:
        active_criteria = await criteria_repo.find_active()
        if active_criteria:
            print(f"Active criteria config: {active_criteria.config_hash}")
            print(f"Criteria: {list(active_criteria.criteria.keys())}")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
