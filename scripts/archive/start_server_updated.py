#!/usr/bin/env python3
"""
Start server with updated .env configuration
"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file with override
load_dotenv(override=True)

# Print the loaded MongoDB URI (first 80 chars for verification)
mongodb_uri = os.getenv("MONGODB_URI", "Not found")
print(f"🔗 Loaded MONGODB_URI: {mongodb_uri[:80]}...")

openai_key = os.getenv("OPENAI_API_KEY", "Not found")
print(f"🔑 Loaded OPENAI_API_KEY: {openai_key[:20]}...")

if __name__ == "__main__":
    print("🚀 Starting Storybench server with updated .env configuration...")
    
    uvicorn.run(
        "src.storybench.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
