"""
Main FastAPI application.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import get_settings
from backend.database import init_db
from backend.api.routes import repos, reviews, health, stats
from backend.api.ws import active_connections, send_progress_update  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting CodeRubric API...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down CodeRubric API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Context-Aware Code Review via RAG - Backend API",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(repos.router, prefix="/api/repos", tags=["repositories"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])

# WebSocket for real-time progress updates


@app.websocket("/ws/review/{review_id}")
async def websocket_review(websocket: WebSocket, review_id: str):
    """WebSocket endpoint for review progress updates."""
    await websocket.accept()
    active_connections[review_id] = websocket
    
    try:
        while True:
            # Keep connection alive, wait for client messages
            _data = await websocket.receive_text()  # noqa: F841
            # Echo back or handle commands
            await websocket.send_json({
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        del active_connections[review_id]
    except Exception as e:
        logger.error(f"WebSocket error for review {review_id}: {e}")
        if review_id in active_connections:
            del active_connections[review_id]


# Serve frontend (if built)
frontend_build_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_build_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_build_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes."""
        index_path = os.path.join(frontend_build_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not built"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api"
    }
