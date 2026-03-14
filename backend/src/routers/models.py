"""Model configuration endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from src.db.session import get_session
from src.db.models import ModelConfig
from src.schemas.base import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/model-configs", response_model=ModelConfigResponse, tags=["Models"])
async def create_model_config(
    config: ModelConfigCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new model configuration."""
    try:
        db_config = ModelConfig(
            provider=config.provider.value,
            model_name=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature
        )
        session.add(db_config)
        await session.commit()
        await session.refresh(db_config)
        
        logger.info(f"Created model config: {db_config.id} ({config.provider}/{config.model_name})")
        return db_config
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating model config: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/model-configs", response_model=list[ModelConfigResponse], tags=["Models"])
async def list_model_configs(session: AsyncSession = Depends(get_session)):
    """List all model configurations."""
    try:
        result = await session.execute(select(ModelConfig))
        configs = result.scalars().all()
        return configs
    except Exception as e:
        logger.error(f"Error listing model configs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-configs/{config_id}", response_model=ModelConfigResponse, tags=["Models"])
async def get_model_config(
    config_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific model configuration."""
    try:
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/model-configs/{config_id}", response_model=ModelConfigResponse, tags=["Models"])
async def update_model_config(
    config_id: int,
    config: ModelConfigUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a model configuration."""
    try:
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        # Update fields if provided
        if config.model_name is not None:
            db_config.model_name = config.model_name
        if config.api_key is not None:
            db_config.api_key = config.api_key
        if config.base_url is not None:
            db_config.base_url = config.base_url
        if config.temperature is not None:
            db_config.temperature = config.temperature
        
        await session.commit()
        await session.refresh(db_config)
        
        logger.info(f"Updated model config: {config_id}")
        return db_config
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating model config: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/model-configs/{config_id}", tags=["Models"])
async def delete_model_config(
    config_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a model configuration."""
    try:
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        await session.delete(db_config)
        await session.commit()
        
        logger.info(f"Deleted model config: {config_id}")
        return {"status": "deleted", "id": config_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting model config: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
