"""
Interview Coach - Main Application Entry Point

Transparent AI Interview Coach Demo
A multi-agent interview coaching system built with Claude Agent SDK.
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api import router

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🎤 Interview Coach starting up...")
    print("📊 Observation panel ready for real-time tracing")
    yield
    # Shutdown
    print("👋 Interview Coach shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Transparent AI Interview Coach",
    description="""
    A multi-agent interview coaching system that provides:
    - 🎯 Simulated English interview practice
    - 📊 Multi-dimensional scoring (Grammar, Content, Fluency, Vocabulary)
    - 💡 Actionable improvement suggestions
    - 🔍 Transparent AI decision observation

    Built with Claude Agent SDK for the Volcengine Winter Conference Demo.
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint - serves the frontend or returns API info."""
    # Check if frontend build exists
    frontend_index = "../frontend/dist/index.html"
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)

    return {
        "message": "Welcome to the Transparent AI Interview Coach",
        "docs": "/docs",
        "api_base": "/api/interview",
        "websocket": "/api/interview/ws/{session_id}",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "interview-coach"}


# Mount static files if frontend is built
frontend_dist = "../frontend/dist"
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=f"{frontend_dist}/assets"), name="assets")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🎤 Transparent AI Interview Coach                          ║
    ║   ─────────────────────────────────────                      ║
    ║                                                              ║
    ║   "每个英语学习者都值得一个透明的 AI 教练"                    ║
    ║                                                              ║
    ║   API Documentation: http://{host}:{port}/docs                ║
    ║   WebSocket Trace:   ws://{host}:{port}/api/interview/ws/     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
    )
