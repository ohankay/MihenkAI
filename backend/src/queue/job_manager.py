"""Job queue management with Redis and RQ."""
import os
import json
import redis
import logging
from rq import Queue

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Initialize Redis connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Initialize RQ queue
job_queue = Queue(connection=redis_client, default_timeout=3600)  # 1 hour timeout


async def enqueue_evaluation_job(job_data: dict) -> str:
    """
    Enqueue an evaluation job to Redis/RQ.
    
    Args:
        job_data: Dictionary containing job information
        
    Returns:
        Job ID
    """
    try:
        job_id = job_data.get('job_id')
        
        # Store job metadata in Redis
        redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps(job_data)
        )
        
        logger.info(f"Enqueued job to Redis: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"Error enqueueing job: {str(e)}")
        raise


async def get_job_data(job_id: str) -> dict:
    """Get job data from Redis."""
    try:
        data = redis_client.get(f"job:{job_id}")
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Error retrieving job data: {str(e)}")
        return None


def cleanup_redis_connection():
    """Close Redis connection."""
    if redis_client:
        redis_client.close()
