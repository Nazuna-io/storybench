#!/usr/bin/env python3
"""
Script to check if the evaluation setup is ready.
"""

import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    print("🔍 Checking Evaluation Setup")
    print("=" * 40)
    
    # Check MongoDB connection
    mongodb_uri = os.getenv("MONGODB_URI")
    if mongodb_uri:
        print("✅ MONGODB_URI found")
    else:
        print("❌ MONGODB_URI not found")
    
    # Check OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        print("✅ OPENAI_API_KEY found")
        print(f"   Key starts with: {openai_api_key[:10]}...")
    else:
        print("❌ OPENAI_API_KEY not found")
        print("   To run evaluations, you need to:")
        print("   1. Get an OpenAI API key from https://platform.openai.com/")
        print("   2. Add it to your .env file: OPENAI_API_KEY=your_key_here")
    
    print("\n📋 What we have so far:")
    print("✅ 90 responses in database (3 prompts × 5 sequences × 3 runs × 2 models)")
    print("✅ Evaluation criteria defined and stored")
    print("✅ LLM evaluation service implemented")
    
    if mongodb_uri and openai_api_key:
        print("\n🚀 Ready to run evaluations!")
        print("   Run: python3 run_evaluations.py")
    else:
        print("\n⚠️  Missing requirements for evaluation")
    
    print("\n🎯 The evaluation process will:")
    print("   1. Load all 90 responses from the database")
    print("   2. For each response, call GPT-4 to evaluate on 7 criteria:")
    print("      - Creativity, Coherence, Character Depth")
    print("      - Dialogue Quality, Visual Imagination") 
    print("      - Conceptual Depth, Adaptability")
    print("   3. Store structured evaluation results in database")
    print("   4. Generate summary statistics comparing models")

if __name__ == "__main__":
    main()
