"""Evaluation endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid
from datetime import datetime
from src.db.session import get_session
from src.db.models import EvaluationJob, EvaluationProfile, ModelConfig
from src.schemas.base import (
    SingleEvalRequest,
    ConversationalEvalRequest,
    JobQueuedResponse,
    JobStatusResponse,
    EvaluationTypeEnum,
    JobStatusEnum
)
from src.job_queue.job_manager import enqueue_evaluation_job

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/evaluate/single", response_model=JobQueuedResponse, tags=["Evaluation"])
async def evaluate_single(
    request: SingleEvalRequest,
    session: AsyncSession = Depends(get_session)
):
    """Start a single evaluation job."""
    try:
        # Verify evaluation profile exists
        result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == request.evaluation_profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Evaluation profile not found")

        # Verify judge LLM profile exists
        mc_result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == request.judge_llm_profile_id)
        )
        if mc_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Judge LLM profile not found")

        # Profile-aware validation:
        # Warn if profile uses context-dependent metrics but no contexts provided.
        # (expected_response is now always required at schema level)
        single_weights = profile.single_weights or {}
        context_metrics = {"faithfulness", "contextual_precision", "contextual_recall",
                           "contextual_relevancy", "hallucination"}
        uses_context_metrics = any(k in single_weights for k in context_metrics)
        if uses_context_metrics and not request.retrieved_contexts:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Bu profil ({', '.join(k for k in single_weights if k in context_metrics)}) "
                    "metriklerini içeriyor; bu metrikler retrieved_contexts gerektirir ancak "
                    "boş liste gönderildi."
                )
            )

        # Generate job ID
        job_id = f"eval-{str(uuid.uuid4())}"
        
        # Create job record
        job = EvaluationJob(
            job_id=job_id,
            profile_id=request.evaluation_profile_id,
            evaluation_type=EvaluationTypeEnum.SINGLE.value,
            status=JobStatusEnum.QUEUED.value
        )
        session.add(job)
        await session.commit()
        
        # Enqueue job to Redis/RQ
        job_data = {
            "job_id": job_id,
            "evaluation_profile_id": request.evaluation_profile_id,
            "judge_llm_profile_id": request.judge_llm_profile_id,
            "evaluation_type": EvaluationTypeEnum.SINGLE.value,
            "prompt": request.prompt,
            "actual_response": request.actual_response,
            "retrieved_contexts": request.retrieved_contexts,
            "expected_response": request.expected_response,
        }
        
        await enqueue_evaluation_job(job_data)
        
        logger.info(f"Queued single evaluation job: {job_id}")
        return JobQueuedResponse(job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error queueing evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evaluate/conversational", response_model=JobQueuedResponse, tags=["Evaluation"])
async def evaluate_conversational(
    request: ConversationalEvalRequest,
    session: AsyncSession = Depends(get_session)
):
    """Start a conversational evaluation job."""
    try:
        # Verify evaluation profile exists
        result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == request.evaluation_profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Evaluation profile not found")

        # Verify judge LLM profile exists
        mc_result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == request.judge_llm_profile_id)
        )
        if mc_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Judge LLM profile not found")
        
        # Generate job ID
        job_id = f"eval-{str(uuid.uuid4())}"
        
        # Create job record
        job = EvaluationJob(
            job_id=job_id,
            profile_id=request.evaluation_profile_id,
            evaluation_type=EvaluationTypeEnum.CONVERSATIONAL.value,
            status=JobStatusEnum.QUEUED.value
        )
        session.add(job)
        await session.commit()
        
        # Convert chat history to dict format
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history
        ]
        
        # Enqueue job to Redis/RQ
        job_data = {
            "job_id": job_id,
            "evaluation_profile_id": request.evaluation_profile_id,
            "judge_llm_profile_id": request.judge_llm_profile_id,
            "evaluation_type": EvaluationTypeEnum.CONVERSATIONAL.value,
            "chat_history": chat_history,
            "prompt": request.prompt,
            "actual_response": request.actual_response,
            "retrieved_contexts": request.retrieved_contexts,
            "scenario": request.scenario,
            "expected_outcome": request.expected_outcome,
        }
        
        await enqueue_evaluation_job(job_data)
        
        logger.info(f"Queued conversational evaluation job: {job_id}")
        return JobQueuedResponse(job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error queueing evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/evaluate/status/{job_id}", response_model=JobStatusResponse, tags=["Evaluation"])
async def get_evaluation_status(
    job_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get evaluation job status and results."""
    try:
        result = await session.execute(
            select(EvaluationJob).where(EvaluationJob.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Return current status
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            composite_score=job.composite_score,
            metrics_breakdown=job.metrics_breakdown,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluate/jobs", tags=["Evaluation"])
async def list_evaluation_jobs(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """List evaluation jobs with pagination."""
    try:
        result = await session.execute(
            select(EvaluationJob).order_by(EvaluationJob.created_at.desc()).limit(limit).offset(offset)
        )
        jobs = result.scalars().all()
        
        return {
            "jobs": jobs,
            "limit": limit,
            "offset": offset,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
