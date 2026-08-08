import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# Primary PostgreSQL / Supabase URL & SQLite Fallback
SQLITE_DB_URL = "sqlite+aiosqlite:///./aura_app.db"
USING_SQLITE = False

def create_db_engine() -> AsyncEngine:
    global USING_SQLITE
    db_url = settings.SUPABASE_DB_URL
    
    if db_url and "postgresql" in db_url:
        try:
            pg_engine = create_async_engine(
                db_url,
                echo=False,
                future=True,
                pool_pre_ping=True,
                poolclass=NullPool,
                connect_args={
                    "prepared_statement_cache_size": 0,
                    "statement_cache_size": 0,
                },
            )
            logger.info(f"Configured PostgreSQL engine for Supabase URL")
            return pg_engine
        except Exception as e:
            logger.warning(f"Failed to create PostgreSQL engine: {e}. Falling back to SQLite.")

    USING_SQLITE = True
    logger.info("Using SQLite fallback engine: aura_app.db")
    return create_async_engine(
        SQLITE_DB_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )

engine = create_db_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def check_and_get_working_engine() -> AsyncEngine:
    """Verify primary engine connection; fallback to SQLite if unreachable."""
    global engine, AsyncSessionLocal, USING_SQLITE
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
        return engine
    except Exception as e:
        logger.warning(f"PostgreSQL connection check failed ({e}). Switching engine to SQLite fallback.")
        USING_SQLITE = True
        engine = create_async_engine(
            SQLITE_DB_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False}
        )
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        return engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    active_engine = await check_and_get_working_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
