"""Database configuration and session management."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://mihenkai_user:secure_password@db:5432/mihenkai_db')

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True,
    poolclass=NullPool,  # Disable connection pooling for flexibility
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database (create tables, run migrations)."""
    # Tables are created by Alembic migrations
    # This is a placeholder for future initialization logic
    pass


async def close_db():
    """Close database connections."""
    await engine.dispose()
