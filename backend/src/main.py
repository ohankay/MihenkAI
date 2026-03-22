"""FastAPI application main entry point."""
import os
import logging
from uuid import uuid4
from fastapi import FastAPI, Request
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
    title="DeepEval based Tester Workbench for LLM Applications",
    description="DeepEval tabanlı LLM uygulama test ve değerlendirme platformu",
    version="0.1.0",
    lifespan=lifespan,
)

# Setup error handlers
setup_error_handlers(app)

# Add CORS middleware
# Development defaults to wildcard for easy LAN testing.
# Production must use explicit origins to avoid accidental open CORS policies.
_cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
if env.lower() == "production" and "*" in _cors_origins:
    raise RuntimeError("CORS_ORIGINS cannot contain '*' in production")

_allow_credentials = "*" not in _cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach request correlation ID for traceability across logs and clients."""
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include routers
app.include_router(config.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(evaluate.router, prefix="/api")


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
