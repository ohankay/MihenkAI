"""Configuration endpoints."""
from fastapi import APIRouter, HTTPException
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "db_config.json"


@router.post("/config", tags=["System"])
async def post_config(config_data: dict):
    """Save configuration for database and redis."""
    try:
        # Ensure config directory exists
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate required fields
        required_fields = ['db_host', 'db_port', 'db_user', 'db_password', 'db_name', 'redis_host', 'redis_port']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Save to file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        
        return {
            "status": "success",
            "message": "Configuration saved successfully",
            "config_file": str(CONFIG_FILE)
        }
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config", tags=["System"])
async def get_config():
    """Get current configuration (without sensitive data)."""
    try:
        if not CONFIG_FILE.exists():
            return {
                "status": "not_configured",
                "message": "System not yet configured",
                "required_fields": ['db_host', 'db_port', 'db_user', 'db_password', 'db_name', 'redis_host', 'redis_port']
            }
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Remove sensitive data from response
        safe_config = {
            'db_host': config.get('db_host'),
            'db_port': config.get('db_port'),
            'db_name': config.get('db_name'),
            'redis_host': config.get('redis_host'),
            'redis_port': config.get('redis_port'),
        }
        
        return {
            "status": "configured",
            "config": safe_config
        }
    except Exception as e:
        logger.error(f"Error retrieving configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", tags=["System"])
async def get_status():
    """Get system status."""
    try:
        # Check if configured
        is_configured = CONFIG_FILE.exists()
        
        return {
            "service": "mihenkai-backend",
            "status": "running",
            "configured": is_configured,
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Error retrieving status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
