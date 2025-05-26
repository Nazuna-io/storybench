#!/usr/bin/env python3
"""
Start server with proper .env loading
"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print the loaded MongoDB URI (first 50 chars for security)
mongodb_uri = os.getenv("MONGODB_URI", "Not found")
print(f"🔗 Loaded MONGODB_URI: {mongodb_uri[:50]}...")

openai_key = os.getenv("OPENAI_API_KEY", "Not found")
print(f"🔑 Loaded OPENAI_API_KEY: {openai_key[:20]}...")

if __name__ == "__main__":
    print("🚀 Starting Storybench server with .env configuration...")
    
    uvicorn.run(
        "src.storybench.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
