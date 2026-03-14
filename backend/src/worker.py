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
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


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
    Process a single evaluation job asynchronously.
    
    Performs the actual evaluation using DeepEval and updates job status in DB.
    
    Args:
        job_id: The evaluation job ID
        
    Returns:
        Result dictionary with status and metrics
    """
    from src.db.models import EvaluationJob, ModelConfig, EvaluationProfile
    from src.evaluator.deepeval_client import DeepEvalClient
    
    logger.info(f"Starting evaluation job {job_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            # Fetch job from database
            result = await session.execute(select(EvaluationJob).filter(EvaluationJob.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found in database")
                return {"status": "FAILED", "job_id": job_id, "error": "Job not found"}
            
            # Mark job as processing
            job.status = "PROCESSING"
            job.started_at = datetime.utcnow()
            await session.commit()
            logger.info(f"Job {job_id} marked as PROCESSING")
            
            try:
                # Fetch model config and profile
                model_config = await session.get(ModelConfig, job.model_config_id)
                evaluation_profile = await session.get(EvaluationProfile, job.evaluation_profile_id)
                
                if not model_config or not evaluation_profile:
                    raise ValueError("Model config or evaluation profile not found")
                
                # Initialize evaluator
                evaluator = DeepEvalClient(
                    model_name=model_config.model_name,
                    model_type=model_config.model_type,
                    api_key=model_config.api_key
                )
                
                # Parse evaluation data
                evaluation_data = json.loads(job.evaluation_data) if isinstance(job.evaluation_data, str) else job.evaluation_data
                
                # Perform evaluation based on type
                if job.evaluation_type == "SINGLE":
                    result = await evaluator.evaluate_single(
                        prompt=evaluation_data.get("prompt", ""),
                        response=evaluation_data.get("response", ""),
                        context=evaluation_data.get("context", ""),
                        profile=evaluation_profile
                    )
                elif job.evaluation_type == "CONVERSATIONAL":
                    result = await evaluator.evaluate_conversational(
                        conversation=evaluation_data.get("conversation", []),
                        context=evaluation_data.get("context", ""),
                        profile=evaluation_profile
                    )
                else:
                    raise ValueError(f"Unknown evaluation type: {job.evaluation_type}")
                
                # Update job with results
                job.status = "COMPLETED"
                job.results = json.dumps(result)
                job.completed_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Job {job_id} completed successfully with score: {result.get('composite_score', 0)}")
                return {
                    "status": "COMPLETED",
                    "job_id": job_id,
                    "metrics": result
                }
                
            except Exception as e:
                # Mark job as failed
                job.status = "FAILED"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                await session.commit()
                
                logger.error(f"Job {job_id} failed during evaluation: {str(e)}")
                return {
                    "status": "FAILED",
                    "job_id": job_id,
                    "error": str(e)
                }
                
    except Exception as e:
        logger.error(f"Critical error processing job {job_id}: {str(e)}")
        return {
            "status": "FAILED",
            "job_id": job_id,
            "error": str(e)
        }


def start_worker():
    """Start the RQ worker."""
    logger.info("Starting RQ Worker...")
    
    # Connect to Redis and create queue
    q = Queue(connection=redis_client)
    
    # Create and start worker
    worker = Worker([q], connection=redis_client)
    
    logger.info("Worker connected to Redis and listening for jobs...")
    worker.work()


if __name__ == "__main__":
    start_worker()


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
    
    session = AsyncSessionLocal()
    
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
        
        # Get job data from Redis
        job_data_str = redis_client.get(f"job:{job_id}")
        if not job_data_str:
            logger.error(f"Job data not found in Redis: {job_id}")
            job.status = "FAILED"
            job.error_message = "Job data not found in Redis"
            await session.commit()
            return {"status": "FAILED", "error": "Job data not found"}
        
        job_data = json.loads(job_data_str)
        
        # Update job status to PROCESSING
        job.status = "PROCESSING"
        await session.commit()
        logger.info(f"Job {job_id} marked as PROCESSING")
        
        # Get profile and model config
        profile_result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == job.profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Profile not found")
        
        model_result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == profile.model_config_id)
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
                expected_response=job_data.get('expected_response'),
                weights=profile.single_weights
            )
        elif job_data['evaluation_type'] == 'CONVERSATIONAL':
            metrics = await evaluator.evaluate_conversational(
                chat_history=job_data['chat_history'],
                prompt=job_data['prompt'],
                actual_response=job_data['actual_response'],
                retrieved_contexts=job_data['retrieved_contexts'],
                weights=profile.conversational_weights
            )
        else:
            raise ValueError(f"Unknown evaluation type: {job_data['evaluation_type']}")
        
        # Calculate composite score
        composite_score = await evaluator.calculate_composite_score(metrics)
        
        # Update job with results
        job.status = "COMPLETED"
        job.composite_score = composite_score
        job.metrics_breakdown = {
            metric_name: {
                "score": metric_data.get("score"),
                "weight": metric_data.get("weight")
            }
            for metric_name, metric_data in metrics.items()
        }
        job.completed_at = datetime.utcnow()
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
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
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
    
    # Create queue and worker
    job_queue = Queue(connection=redis_client)
    worker = Worker([job_queue], connection=redis_client)
    
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
