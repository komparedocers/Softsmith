"""
Database configuration and session management.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from .config import get_config
from .logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

# Engine and session maker (initialized on startup)
engine = None
async_session_maker = None


def init_db():
    """Initialize database engine and session maker."""
    global engine, async_session_maker

    config = get_config()
    db_config = config.database

    logger.info(
        "Initializing database",
        url=db_config.url.split('@')[-1],  # Hide credentials
        pool_size=db_config.pool_size,
    )

    engine = create_async_engine(
        db_config.url,
        echo=db_config.echo,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_pre_ping=True,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    logger.warning("Dropping all database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
