"""
Main FastAPI application for Software Maker Platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_config
from app.core.db import init_db, create_tables
from app.core.logging import setup_logging, get_logger
from app.core.task_queue import init_celery
from app.api.routers import projects, tasks, config, agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger = get_logger(__name__)
    logger.info("Starting Software Maker Platform API")

    # Initialize components
    setup_logging()
    init_db()
    init_celery()

    # Create database tables
    await create_tables()

    logger.info("API startup complete")

    yield

    logger.info("API shutting down")


# Create FastAPI app
app = FastAPI(
    title="Software Maker Platform API",
    description="AI-powered software generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(config.router)
app.include_router(agents.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Software Maker Platform API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
