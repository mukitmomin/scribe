from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.v1 import papers, chat, scribe
from app.routers.public import blog

app = FastAPI(
    title="Scribe API",
    description="AI Research Assistant Backend - Paper discovery, learning, and blog drafting",
    version="1.0.0"
)

# CORS middleware configured from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API routers (v1)
app.include_router(papers.router)
app.include_router(chat.router)
app.include_router(scribe.router)

# Public API for external consumption (e.g., portfolio blog)
app.include_router(blog.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Scribe API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
