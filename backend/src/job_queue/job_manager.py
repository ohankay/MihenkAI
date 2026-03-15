"""Job queue management with Redis and RQ."""
# Note: this package is named job_queue (not queue) to avoid shadowing Python stdlib queue module
import os
import json
import redis
import logging
from rq import Queue

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Redis client for plain JSON metadata (decode_responses=True for string convenience)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Separate Redis client for RQ — must NOT have decode_responses=True because
# RQ serializes job arguments with pickle (binary). decode_responses=True would
# cause UnicodeDecodeError when the worker tries to read those bytes back.
rq_redis_client = redis.from_url(REDIS_URL, decode_responses=False)

# Initialize RQ queue using the binary-safe connection
job_queue = Queue(connection=rq_redis_client, default_timeout=3600)  # 1 hour timeout


async def enqueue_evaluation_job(job_data: dict) -> str:
    """
    Enqueue an evaluation job to Redis/RQ.
    
    Args:
        job_data: Dictionary containing job information
        
    Returns:
        Job ID
    """
    try:
        from src.worker import process_evaluation_job_sync
        
        job_id = job_data.get('job_id')
        
        # Store job metadata in Redis
        redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps(job_data)
        )
        
        # Enqueue the job to RQ
        rq_job = job_queue.enqueue(
            process_evaluation_job_sync,
            args=(job_id,),
            job_id=f"rq:{job_id}",
            timeout=3600
        )
        
        logger.info(f"Enqueued job to RQ: {job_id} (RQ job: {rq_job.id})")
        return job_id
    except Exception as e:
        logger.error(f"Error enqueueing job: {str(e)}")
        raise


async def get_job_data(job_id: str) -> dict:
    """Get job data from Redis and RQ status."""
    try:
        from rq.job import Job
        
        data = redis_client.get(f"job:{job_id}")
        result = json.loads(data) if data else None
        
        # Get RQ job status
        try:
            rq_job = Job.fetch(f"rq:{job_id}", connection=redis_client)
            if result:
                result['rq_status'] = rq_job.get_status()
                result['rq_result'] = rq_job.result
        except Exception as e:
            logger.debug(f"Could not fetch RQ job status: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving job data: {str(e)}")
        return None


def cleanup_redis_connection():
    """Close Redis connection."""
    if redis_client:
        redis_client.close()
