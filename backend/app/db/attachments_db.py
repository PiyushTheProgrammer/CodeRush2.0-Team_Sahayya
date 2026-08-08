import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.session import check_and_get_working_engine

logger = logging.getLogger(__name__)

async def init_attachments_table() -> None:
    """Ensure aura_attachments table exists in Database on application startup."""
    active_engine = await check_and_get_working_engine()
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS aura_attachments (
        file_id VARCHAR(64) PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        extracted_passages_count INTEGER DEFAULT 1,
        summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        async with active_engine.begin() as conn:
            await conn.execute(text(create_table_sql))
        logger.info("Database 'aura_attachments' table initialized successfully.")
    except Exception as e:
        logger.warning(f"Database aura_attachments table initialization notice: {e}")


async def save_attachment_db(
    file_id: str,
    user_email: str,
    filename: str,
    file_size_bytes: int,
    extracted_passages_count: int,
    summary: str
) -> Optional[Dict[str, Any]]:
    """Insert new document attachment into aura_attachments table."""
    active_engine = await check_and_get_working_engine()
    sql = text("""
        INSERT INTO aura_attachments (file_id, user_email, filename, file_size_bytes, extracted_passages_count, summary)
        VALUES (:file_id, :user_email, :filename, :file_size_bytes, :extracted_passages_count, :summary);
    """)
    try:
        async with active_engine.begin() as conn:
            await conn.execute(sql, {
                "file_id": file_id,
                "user_email": user_email.lower().strip(),
                "filename": filename,
                "file_size_bytes": file_size_bytes,
                "extracted_passages_count": extracted_passages_count,
                "summary": summary
            })
        return {
            "file_id": file_id,
            "user_email": user_email,
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "extracted_passages_count": extracted_passages_count,
            "summary": summary
        }
    except Exception as e:
        logger.warning(f"Database save_attachment_db error: {e}")
    return None
