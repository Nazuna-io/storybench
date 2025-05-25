"""FastAPI main application for Storybench Web UI."""

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager
# Make sure this import path is correct for your project structure
from storybench.database.connection import init_database, close_database
from .api import models, prompts, evaluations, results, validation, sse, criteria

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("INFO:     Initializing database connection...")
    try:
        await init_database()
        print("INFO:     Database connection initialized.")
    except Exception as e:
        print(f"ERROR:    Failed to initialize database: {type(e).__name__}: {e}")
        print(f"ERROR:    Full exception details: {repr(e)}")
        # Re-raise the exception to prevent the app from starting with a broken database
        raise
    yield
    # Code to run on shutdown
    print("INFO:     Closing database connection...")
    try:
        await close_database()
        print("INFO:     Database connection closed.")
    except Exception as e:
        print(f"ERROR:    Failed to close database: {type(e).__name__}: {e}")
        print(f"ERROR:    Full exception details: {repr(e)}")

# Create FastAPI app
app = FastAPI(
    title="Storybench Web UI",
    description="Web interface for the Storybench LLM creativity evaluation system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan  # Add this line
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175", "http://localhost:3000"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(models.router, prefix="/api/config", tags=["Configuration"])
app.include_router(prompts.router, prefix="/api/config", tags=["Configuration"])
app.include_router(criteria.router, prefix="/api/config", tags=["Configuration"])
app.include_router(validation.router, prefix="/api/config", tags=["Configuration"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(sse.router, prefix="/api/sse", tags=["Server-Sent Events"])

# Setup SSE callbacks for real-time updates
from .api.sse import setup_sse_callbacks
# Note: SSE callbacks now use dependency injection instead of global service
# setup_sse_callbacks() # Disabled until SSE is updated for database architecture

# Serve static files (frontend build) when running in production
frontend_path = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
    
    @app.get("/")
    async def read_index():
        return FileResponse(str(frontend_path / "index.html"))
    
    @app.get("/{path:path}")
    async def read_spa(path: str):
        # Serve static files or fallback to index.html for SPA routing
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_path / "index.html"))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "storybench-web"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


def main():
    """Entry point for storybench-web CLI command."""
    import uvicorn
    uvicorn.run("storybench.web.main:app", host="0.0.0.0", port=8000, reload=True)
