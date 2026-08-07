import logging
from sqlalchemy import text

from app.db.session import engine

logger = logging.getLogger(__name__)


async def init_pgvector() -> None:
    """Ensure pgvector extension is enabled in PostgreSQL / Supabase on application startup."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        logger.info("pgvector extension initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize pgvector extension: {e}")
        raise RuntimeError(f"Database pgvector initialization failed: {e}") from e
