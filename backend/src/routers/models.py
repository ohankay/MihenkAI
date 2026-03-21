"""Model configuration endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging
import time
import asyncio
from datetime import datetime, timedelta, timezone
from src.db.session import get_session
from src.db.models import ModelConfig, LLMQueryLog
from src.schemas.base import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    ModelChatTestRequest,
    ModelChatTestResponse,
    LLMQueryLogSummaryResponse,
    LLMQueryLogDetailResponse,
    LLMQueryLogListResponse,
)
from src.evaluator.deepeval_client import DeepEvalClient

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_utc_naive(value: datetime) -> datetime:
    """Normalize datetime to UTC naive to match DB TIMESTAMP WITHOUT TIME ZONE."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


@router.post("/model-configs", response_model=ModelConfigResponse, tags=["Models"])
async def create_model_config(
    config: ModelConfigCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new model configuration."""
    try:
        # Enforce unique profile name
        if config.name:
            dup = await session.execute(
                select(ModelConfig).where(func.lower(ModelConfig.name) == func.lower(config.name))
            )
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=409, detail=f"A judge LLM profile named '{config.name}' already exists.")
        db_config = ModelConfig(
            name=config.name,
            provider=config.provider.value,
            model_name=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            generation_kwargs=config.generation_kwargs
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
        if config.name is not None:
            dup = await session.execute(
                select(ModelConfig).where(
                    func.lower(ModelConfig.name) == func.lower(config.name),
                    ModelConfig.id != config_id,
                )
            )
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=409, detail=f"A judge LLM profile named '{config.name}' already exists.")
            db_config.name = config.name
        if config.provider is not None:
            db_config.provider = config.provider.value
        if config.model_name is not None:
            db_config.model_name = config.model_name
        if config.api_key is not None:
            db_config.api_key = config.api_key
        if config.base_url is not None:
            db_config.base_url = config.base_url
        if config.temperature is not None:
            db_config.temperature = config.temperature
        if config.generation_kwargs is not None:
            db_config.generation_kwargs = config.generation_kwargs
        
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


@router.post("/model-configs/{config_id}/test-chat", response_model=ModelChatTestResponse, tags=["Models"])
async def test_model_chat(
    config_id: int,
    request: ModelChatTestRequest,
    session: AsyncSession = Depends(get_session)
):
    """Run a simple prompt against selected model profile to verify integration/health."""
    try:
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == config_id)
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            raise HTTPException(status_code=404, detail="Model config not found")

        evaluator = DeepEvalClient(db_config)

        start = time.perf_counter()
        answer = await asyncio.to_thread(evaluator.judge.generate, request.prompt)
        latency_ms = int((time.perf_counter() - start) * 1000)

        return ModelChatTestResponse(
            model_config_id=db_config.id,
            provider=db_config.provider,
            model_name=db_config.model_name,
            prompt=request.prompt,
            response=answer or "",
            latency_ms=latency_ms,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing model chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/model-configs/{config_id}/query-logs", response_model=LLMQueryLogListResponse, tags=["Models"])
async def list_model_query_logs(
    config_id: int,
    limit: int = 15,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List recent query logs for a model config in a datetime range."""
    try:
        cfg_result = await session.execute(
            select(ModelConfig.id).where(ModelConfig.id == config_id)
        )
        if cfg_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Model config not found")

        clamped_limit = max(1, min(limit, 100))
        end_dt = _to_utc_naive(end_time) if end_time else datetime.utcnow()
        start_dt = _to_utc_naive(start_time) if start_time else (end_dt - timedelta(hours=1))

        if start_dt > end_dt:
            raise HTTPException(status_code=422, detail="start_time cannot be greater than end_time")

        result = await session.execute(
            select(LLMQueryLog)
            .where(LLMQueryLog.model_config_id == config_id)
            .where(LLMQueryLog.created_at >= start_dt)
            .where(LLMQueryLog.created_at <= end_dt)
            .order_by(LLMQueryLog.created_at.desc())
            .limit(clamped_limit)
        )
        rows = result.scalars().all()

        return LLMQueryLogListResponse(
            items=[LLMQueryLogSummaryResponse.model_validate(row) for row in rows],
            limit=clamped_limit,
            count=len(rows),
            start_time=start_dt,
            end_time=end_dt,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing model query logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-configs/{config_id}/query-logs/{log_id}", response_model=LLMQueryLogDetailResponse, tags=["Models"])
async def get_model_query_log_detail(
    config_id: int,
    log_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get full input/output payload for one query log row."""
    try:
        result = await session.execute(
            select(LLMQueryLog)
            .where(LLMQueryLog.id == log_id)
            .where(LLMQueryLog.model_config_id == config_id)
        )
        row = result.scalar_one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Query log not found")

        return LLMQueryLogDetailResponse.model_validate(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model query log detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
