"""Configuration endpoints."""
from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config", tags=["System"])
async def get_config():
    """Get current configuration status.
    
    Database and Redis are configured automatically via Docker environment variables.
    """
    return {"status": "configured"}


@router.get("/status", tags=["System"])
async def get_status():
    """Get system status."""
    try:
        return {
            "service": "mihenkai-backend",
            "status": "running",
            "configured": True,
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Error retrieving status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
