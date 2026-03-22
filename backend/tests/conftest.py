"""Pytest configuration and fixtures."""
import asyncio
import logging
import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.db.models import EvaluationJob, EvaluationProfile, LLMQueryLog, ModelConfig
from src.db.session import AsyncSessionLocal

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_ENTITY_PREFIX = "AUTOTEST_CLEANUP_"

logger = logging.getLogger(__name__)


async def _cleanup_test_definitions() -> dict:
    """Delete test-created records identified by TEST_ENTITY_PREFIX."""
    stats = {
        "jobs_deleted": 0,
        "profiles_deleted": 0,
        "logs_deleted": 0,
        "models_deleted": 0,
    }

    async with AsyncSessionLocal() as session:
        profile_ids = list(
            (await session.execute(
                select(EvaluationProfile.id).where(EvaluationProfile.name.ilike(f"{TEST_ENTITY_PREFIX}%"))
            )).scalars().all()
        )
        if profile_ids:
            job_result = await session.execute(
                delete(EvaluationJob).where(EvaluationJob.profile_id.in_(profile_ids))
            )
            stats["jobs_deleted"] = int(job_result.rowcount or 0)

            profile_result = await session.execute(
                delete(EvaluationProfile).where(EvaluationProfile.id.in_(profile_ids))
            )
            stats["profiles_deleted"] = int(profile_result.rowcount or 0)

        model_ids = list(
            (await session.execute(
                select(ModelConfig.id).where(ModelConfig.name.ilike(f"{TEST_ENTITY_PREFIX}%"))
            )).scalars().all()
        )
        if model_ids:
            log_result = await session.execute(
                delete(LLMQueryLog).where(LLMQueryLog.model_config_id.in_(model_ids))
            )
            stats["logs_deleted"] = int(log_result.rowcount or 0)

            model_result = await session.execute(
                delete(ModelConfig).where(ModelConfig.id.in_(model_ids))
            )
            stats["models_deleted"] = int(model_result.rowcount or 0)

        await session.commit()

    return stats


def pytest_sessionfinish(session, exitstatus):
    """Cleanup test-created DB definitions only if all tests pass."""
    if exitstatus != 0:
        logger.info("Skipping test definition cleanup because test session failed.")
        return

    try:
        stats = asyncio.run(_cleanup_test_definitions())
        logger.info(
            "Test definition cleanup completed: jobs=%s profiles=%s logs=%s models=%s",
            stats["jobs_deleted"],
            stats["profiles_deleted"],
            stats["logs_deleted"],
            stats["models_deleted"],
        )
    except Exception as exc:
        # Cleanup should never mask test result.
        logger.warning("Test definition cleanup failed: %s", exc)


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create tables
    async with engine.begin() as conn:
        from src.db.models import Base
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    AsyncTestSession = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with AsyncTestSession() as session:
        yield session


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    mock = MagicMock()
    mock.setex = MagicMock()
    mock.get = MagicMock()
    mock.delete = MagicMock()
    return mock


@pytest.fixture
def mock_deepeval_client():
    """Create mock DeepEval client."""
    mock = MagicMock()
    mock.evaluate_single = AsyncMock(return_value={
        'faithfulness': 85.0,
        'relevancy': 90.0,
        'completeness': 88.0,
        'composite_score': 87.67
    })
    mock.evaluate_conversational = AsyncMock(return_value={
        'faithfulness': 82.0,
        'relevancy': 88.0,
        'knowledge_retention': 91.0,
        'completeness': 85.0,
        'composite_score': 86.5
    })
    return mock


@pytest.fixture
def sample_model_config_data():
    """Sample model configuration data."""
    return {
        'model_name': 'gpt-4',
        'model_type': 'openai',
        'api_key': 'test-key-12345',
    }


@pytest.fixture
def sample_profile_data():
    """Sample evaluation profile data."""
    return {
        'name': 'Standard Profile',
        'description': 'Standard evaluation weights',
        'faithfulness_weight': 0.30,
        'relevancy_weight': 0.35,
        'completeness_weight': 0.35,
        'knowledge_retention_weight': 0.0,
    }


@pytest.fixture
def sample_single_evaluation_data():
    """Sample single evaluation data."""
    return {
        'prompt': 'What is the capital of France?',
        'response': 'The capital of France is Paris, located in the northern-central region of the country.',
        'context': 'France is a country in Western Europe with Paris as its capital.',
    }


@pytest.fixture
def sample_conversational_data():
    """Sample conversational evaluation data."""
    return {
        'conversation': [
            {'role': 'user', 'content': 'What is the capital of France?'},
            {'role': 'assistant', 'content': 'The capital of France is Paris.'},
            {'role': 'user', 'content': 'When was it founded?'},
            {'role': 'assistant', 'content': 'Paris was founded in 250 BCE.'},
        ],
        'context': 'Paris is the capital and largest city of France.',
    }
