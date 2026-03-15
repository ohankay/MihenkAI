"""FastAPI application main entry point."""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.db.session import init_db, close_db
from src.routers import config, models, profiles, evaluate
from src.logging_config import setup_logging, get_logger
from src.error_handling import setup_error_handlers

# Setup structured logging
env = os.getenv("ENVIRONMENT", "development")
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(env=env, log_level=log_level)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for app startup and shutdown."""
    # Startup
    logger.info("Starting MihenkAI application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MihenkAI application...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="MihenkAI - LLM Evaluation System",
    description="Automatic evaluation system for LLM responses",
    version="0.1.0",
    lifespan=lifespan,
)

# Setup error handlers
setup_error_handlers(app)

# Add CORS middleware
# Note: allow_credentials=True is incompatible with allow_origins=["*"].
# Set CORS_ORIGINS env var to a comma-separated list of specific origins in production.
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(profiles.router, prefix="/api", tags=["profiles"])
app.include_router(evaluate.router, prefix="/api", tags=["evaluate"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mihenkai-backend"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MihenkAI - LLM Evaluation System",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
