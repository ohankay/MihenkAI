"""RQ Worker for processing evaluation jobs."""
import asyncio
import os
import logging
import json
from datetime import datetime
from rq import Queue, Worker
import redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://mihenkai_user:secure_password@db:5432/mihenkai_db')

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Redis setup
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
# decode_responses=True for JSON metadata reads (job:{job_id} keys)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
# decode_responses=False for RQ — pickle-serialized job data is binary
rq_redis_client = redis.from_url(REDIS_URL, decode_responses=False)


def process_evaluation_job_sync(job_id: str) -> dict:
    """
    Synchronous wrapper for async job processing (RQ-compatible).
    
    Args:
        job_id: The evaluation job ID
        
    Returns:
        Result dictionary
    """
    try:
        # Run the async function in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_evaluation_job(job_id))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Wrapper error for job {job_id}: {str(e)}")
        return {"status": "FAILED", "job_id": job_id, "error": str(e)}


async def process_evaluation_job(job_id: str) -> dict:
    """
    Process an evaluation job.
    
    Args:
        job_id: The evaluation job ID
        
    Returns:
        Result dictionary with scores and metrics
    """
    from src.db.models import EvaluationJob, EvaluationProfile, ModelConfig
    from src.evaluator.deepeval_client import DeepEvalClient
    from src.schemas.base import JobStatusEnum
    from src.services.job_lifecycle import apply_transition, can_transition
    
    session = AsyncSessionLocal()
    job = None
    
    try:
        logger.info(f"Processing job: {job_id}")
        
        # Get job record
        result = await session.execute(
            select(EvaluationJob).where(EvaluationJob.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            return {"status": "FAILED", "error": "Job not found"}

        if job.status == JobStatusEnum.ABORTED.value:
            return {"status": JobStatusEnum.ABORTED.value, "job_id": job_id, "error": "Aborted by user"}
        
        # Get job data from Redis
        job_data_str = redis_client.get(f"job:{job_id}")
        if not job_data_str:
            logger.error(f"Job data not found in Redis: {job_id}")
            job.status = "FAILED"
            job.error_message = "Job data not found in Redis"
            await session.commit()
            return {"status": "FAILED", "error": "Job data not found"}
        
        job_data = json.loads(job_data_str)

        if redis_client.get(f"abort:{job_id}"):
            apply_transition(
                job,
                JobStatusEnum.ABORTED.value,
                error_message="Aborted by user",
                result_payload={
                    "status": JobStatusEnum.ABORTED.value,
                    "error": "Aborted by user",
                },
            )
            await session.commit()
            return {"status": JobStatusEnum.ABORTED.value, "job_id": job_id, "error": "Aborted by user"}
        
        # Update job status to PROCESSING
        apply_transition(job, JobStatusEnum.PROCESSING.value, set_completed_at=False)
        await session.commit()
        logger.info(f"Job {job_id} marked as {JobStatusEnum.PROCESSING.value}")
        
        # Get profile and model config
        profile_result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == job.profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Profile not found")
        
        # judge_llm_profile_id is required — provided by caller in job_data
        effective_model_config_id = job_data.get('judge_llm_profile_id')
        if not effective_model_config_id:
            raise ValueError("judge_llm_profile_id is required in job_data")
        model_result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == effective_model_config_id)
        )
        model_config = model_result.scalar_one_or_none()
        
        if not model_config:
            raise ValueError("Model config not found")
        
        logger.info(f"Using model: {model_config.provider}/{model_config.model_name}")
        
        # Initialize DeepEval client
        evaluator = DeepEvalClient(model_config)
        
        # Run evaluation based on type
        if job_data['evaluation_type'] == 'SINGLE':
            metrics = await evaluator.evaluate_single(
                prompt=job_data['prompt'],
                actual_response=job_data['actual_response'],
                retrieved_contexts=job_data['retrieved_contexts'],
                expected_response=job_data['expected_response'],
                weights=profile.single_weights,
                negative_thresholds=profile.single_negative_thresholds or {},
            )
        elif job_data['evaluation_type'] == 'CONVERSATIONAL':
            metrics = await evaluator.evaluate_conversational(
                chat_history=job_data['chat_history'],
                prompt=job_data['prompt'],
                actual_response=job_data['actual_response'],
                retrieved_contexts=job_data['retrieved_contexts'],
                weights=profile.conversational_weights,
                scenario=job_data.get('scenario'),
                expected_outcome=job_data.get('expected_outcome'),
            )
        else:
            raise ValueError(f"Unknown evaluation type: {job_data['evaluation_type']}")
        
        # Calculate composite score
        composite_score = await evaluator.calculate_composite_score(metrics)

        if redis_client.get(f"abort:{job_id}"):
            apply_transition(
                job,
                JobStatusEnum.ABORTED.value,
                error_message="Aborted by user",
                result_payload={
                    "status": JobStatusEnum.ABORTED.value,
                    "error": "Aborted by user",
                },
            )
            await session.commit()
            return {"status": JobStatusEnum.ABORTED.value, "job_id": job_id, "error": "Aborted by user"}
        
        # Update job with results
        apply_transition(job, JobStatusEnum.COMPLETED.value)
        job.composite_score = composite_score
        # Store full metric data so penalty metrics (threshold, negative, exceeded) are preserved.
        job.metrics_breakdown = {
            metric_name: {k: v for k, v in metric_data.items()}
            for metric_name, metric_data in metrics.items()
        }
        job.result_payload = {
            "status": "COMPLETED",
            "composite_score": composite_score,
            "metrics_breakdown": job.metrics_breakdown,
        }
        await session.commit()
        
        logger.info(f"Job {job_id} completed with score: {composite_score}")
        
        return {
            "status": "COMPLETED",
            "job_id": job_id,
            "composite_score": composite_score,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {str(e)}")
        if job is not None:
            if can_transition(job.status, JobStatusEnum.FAILED.value):
                apply_transition(
                    job,
                    JobStatusEnum.FAILED.value,
                    error_message=str(e),
                    result_payload={
                        "status": JobStatusEnum.FAILED.value,
                        "error": str(e),
                    },
                )
            await session.commit()
        
        return {
            "status": "FAILED",
            "job_id": job_id,
            "error": str(e)
        }
    finally:
        await session.close()


def main():
    """Main worker loop."""
    logger.info("Starting MihenkAI Worker...")
    logger.info(f"Redis URL: {REDIS_URL}")
    logger.info(f"Database URL: {DATABASE_URL}")
    
    # Create queue and worker using binary-safe RQ connection
    job_queue = Queue(connection=rq_redis_client)
    worker = Worker([job_queue], connection=rq_redis_client)
    
    logger.info("Worker listening for jobs...")
    
    try:
        # Start the worker loop
        worker.work(with_scheduler=False)
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
    finally:
        logger.info("Worker shutting down...")
        redis_client.close()


if __name__ == "__main__":
    main()
