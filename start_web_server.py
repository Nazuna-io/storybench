#!/usr/bin/env python3
"""Start the Storybench web server for testing."""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ.setdefault("MONGODB_URI", "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")

import uvicorn
from storybench.web.main import app

if __name__ == "__main__":
    print("Starting Storybench web server...")
    print("Local Models page: http://localhost:8000/local-models")
    print("API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_level="info",
        reload=False
    )
