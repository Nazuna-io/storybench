#!/usr/bin/env python3
"""
Storybench End-to-End Production Test
====================================
Tests exactly 12 frontier models as specified in test plan:
- 12 models × 45 responses each = 540 total responses
- Temperature 1.0 for prompts, 0.3 for evaluation
- 7 evaluation criteria per response
- Skip models with API problems and continue
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storybench.clients.directus_client import DirectusClient
from storybench.database.connection import DatabaseConnection
from storybench.evaluators.api_evaluator import APIEvaluator


# TEST PLAN MODELS - Exactly 12 models as specified
TEST_PLAN_MODELS = [
    {"provider": "anthropic", "model_name": "claude-opus-4-20250514"},
    {"provider": "anthropic", "model_name": "claude-sonnet-4-20250514"},
    {"provider": "anthropic", "model_name": "claude-3-7-sonnet-20250219"},
    {"provider": "openai", "model_name": "gpt-4.1"},
    {"provider": "openai", "model_name": "gpt-4o"},
    {"provider": "openai", "model_name": "o4-mini"},
    {"provider": "gemini", "model_name": "gemini-2.5-flash-preview-05-20"},
    {"provider": "gemini", "model_name": "gemini-2.5-pro-preview-05-06"},
    {"provider": "deepinfra", "model_name": "Qwen/Qwen3-235B-A22B"},
    {"provider": "deepinfra", "model_name": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
    {"provider": "deepinfra", "model_name": "deepseek-ai/DeepSeek-R1"},
    {"provider": "deepinfra", "model_name": "deepseek-ai/DeepSeek-V3-0324"}
]


def validate_environment():
    """Validate required environment variables."""
    required_vars = {
        "DIRECTUS_URL": "Directus CMS URL",
        "DIRECTUS_TOKEN": "Directus API token", 
        "MONGODB_URI": "MongoDB connection string",
        "GOOGLE_API_KEY": "Google Gemini API key for evaluation",
        "ANTHROPIC_API_KEY": "Anthropic API key",
        "OPENAI_API_KEY": "OpenAI API key",
        "DEEPINFRA_API_KEY": "Deepinfra API key"
    }
    
    missing = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({desc})")
    
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)
    
    print("✅ Environment variables validated")


async def setup_api_keys() -> Dict[str, str]:
    """Setup API keys for all providers."""
    api_keys = {
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "deepinfra": os.getenv("DEEPINFRA_API_KEY")
    }
    
    print(f"\n🔑 API KEYS SETUP")
    print("-" * 50)
    
    for provider, key in api_keys.items():
        if key:
            print(f"   ✅ {provider}: API key configured")
        else:
            print(f"   ❌ {provider}: No API key found")
    
    return api_keys