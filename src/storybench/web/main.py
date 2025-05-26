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
from .api import models, prompts, evaluations, results, validation, criteria, local_models, hardware_info
from .api import sse_database as sse
from .api import sse_results
from .services.background_evaluation_service import start_background_service, stop_background_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    pass

# --- FastAPI startup event for background tasks ---

    # Code to run on startup
    print("INFO:     Initializing database connection...")
    try:
        await init_database()
        print("INFO:     Database connection initialized.")
        
        # Start background evaluation service
        print("INFO:     Starting background evaluation service (after DB init)...")
        # Force reset the global background service so it is recreated after DB is ready
        from storybench.web.services import background_evaluation_service as bes
        bes._background_service = None
        import asyncio
        from storybench.web.services.background_evaluation_service import start_background_service
        try:
            asyncio.create_task(start_background_service())
            print("INFO:     Background evaluation service started (via lifespan).");
            # Minimal heartbeat test
            async def test_heartbeat():
                import logging
                while True:
                    print("[TEST_HEARTBEAT] Minimal background task is running...")
                    logging.info("[TEST_HEARTBEAT] Minimal background task is running...")
                    await asyncio.sleep(2)
            asyncio.create_task(test_heartbeat())
        except Exception as e:
            print(f"ERROR:    Failed to start background evaluation service: {type(e).__name__}: {e}")
            print(f"ERROR:    Full exception details: {repr(e)}")
        
    except Exception as e:
        print(f"ERROR:    Failed to initialize database: {type(e).__name__}: {e}")
        print(f"ERROR:    Full exception details: {repr(e)}")
        print("WARNING:  Server will start without database connection.")
        print("WARNING:  Some features may not work until database is available.")
        # Don't raise the exception - allow server to start
    yield
    # Code to run on shutdown
    print("INFO:     Closing database connection...")
    try:
        # Stop background evaluation service first
        print("INFO:     Stopping background evaluation service...")
        await stop_background_service()
        print("INFO:     Background evaluation service stopped.")
        
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
    lifespan=lifespan
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
app.include_router(local_models.router, prefix="/api", tags=["Local Models"])
app.include_router(hardware_info.router, prefix="/api", tags=["Hardware Info"])
app.include_router(sse.router, prefix="/api/sse", tags=["Server-Sent Events"])
app.include_router(sse_results.router, prefix="/api/sse", tags=["Server-Sent Events"])

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "storybench-web"}

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
        # Don't serve SPA for API routes - let them be handled by the API routers
        if path.startswith("api/"):
            # This shouldn't be reached since API routes are handled by routers
            # But just in case, we'll raise a 404
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API endpoint not found")
            
        # Serve static files or fallback to index.html for SPA routing
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_path / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


def main():
    """Entry point for storybench-web CLI command."""
    import uvicorn
    uvicorn.run("storybench.web.main:app", host="0.0.0.0", port=8000, reload=True)
