import json
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from app.db.session import check_and_get_working_engine

logger = logging.getLogger(__name__)

async def init_chat_history_table() -> None:
    """Ensure aura_chat_history table exists in PostgreSQL / SQLite on application startup."""
    active_engine = await check_and_get_working_engine()
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS aura_chat_history (
        task_id VARCHAR(64) PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        user_prompt TEXT NOT NULL,
        synthesized_answer TEXT NOT NULL,
        passages_json TEXT,
        claims_json TEXT,
        attachments_json TEXT DEFAULT '[]',
        is_saved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        async with active_engine.begin() as conn:
            await conn.execute(text(create_table_sql))
        logger.info("Database 'aura_chat_history' table initialized successfully.")
    except Exception as e:
        logger.warning(f"Database aura_chat_history table initialization notice: {e}")


async def save_chat_session_db(
    task_id: str,
    user_email: str,
    user_prompt: str,
    synthesized_answer: str,
    passages_json: str = "[]",
    claims_json: str = "[]",
    attachments_json: str = "[]",
    is_saved: bool = False
) -> Optional[Dict[str, Any]]:
    """Save or update research chat activity into aura_chat_history table."""
    active_engine = await check_and_get_working_engine()
    
    # Try check existing first for SQLite / PG compatibility
    sql_check = text("SELECT task_id FROM aura_chat_history WHERE task_id = :task_id;")
    sql_update = text("""
        UPDATE aura_chat_history SET
            user_email = :user_email,
            user_prompt = :user_prompt,
            synthesized_answer = :synthesized_answer,
            passages_json = :passages_json,
            claims_json = :claims_json,
            attachments_json = :attachments_json,
            is_saved = :is_saved
        WHERE task_id = :task_id;
    """)
    sql_insert = text("""
        INSERT INTO aura_chat_history (task_id, user_email, user_prompt, synthesized_answer, passages_json, claims_json, attachments_json, is_saved)
        VALUES (:task_id, :user_email, :user_prompt, :synthesized_answer, :passages_json, :claims_json, :attachments_json, :is_saved);
    """)

    params = {
        "task_id": task_id,
        "user_email": user_email.lower().strip(),
        "user_prompt": user_prompt,
        "synthesized_answer": synthesized_answer,
        "passages_json": passages_json,
        "claims_json": claims_json,
        "attachments_json": attachments_json,
        "is_saved": is_saved
    }

    try:
        async with active_engine.begin() as conn:
            check_res = await conn.execute(sql_check, {"task_id": task_id})
            if check_res.fetchone():
                await conn.execute(sql_update, params)
            else:
                await conn.execute(sql_insert, params)

        return {
            "task_id": task_id,
            "user_email": user_email,
            "user_prompt": user_prompt,
            "synthesized_answer": synthesized_answer,
            "is_saved": is_saved
        }
    except Exception as e:
        logger.warning(f"Database save_chat_session error: {e}")
    return None


async def toggle_save_chat_db(task_id: str, is_saved: bool) -> bool:
    """Toggle bookmark saved state for a research chat in Database."""
    active_engine = await check_and_get_working_engine()
    sql = text("UPDATE aura_chat_history SET is_saved = :is_saved WHERE task_id = :task_id;")
    try:
        async with active_engine.begin() as conn:
            result = await conn.execute(sql, {"task_id": task_id, "is_saved": is_saved})
            return result.rowcount > 0
    except Exception as e:
        logger.warning(f"Database toggle_save_chat error: {e}")
        return False


async def get_user_activity_history_db(user_email: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Retrieve recent research activity history for a user from Database."""
    active_engine = await check_and_get_working_engine()
    sql = text("""
        SELECT task_id, user_email, user_prompt, synthesized_answer, passages_json, claims_json, attachments_json, is_saved, created_at
        FROM aura_chat_history
        WHERE LOWER(user_email) = LOWER(:user_email)
        ORDER BY created_at DESC
        LIMIT :limit;
    """)
    records = []
    try:
        async with active_engine.connect() as conn:
            result = await conn.execute(sql, {"user_email": user_email.lower().strip(), "limit": limit})
            rows = result.fetchall()
            for r in rows:
                records.append({
                    "task_id": r[0],
                    "user_email": r[1],
                    "user_prompt": r[2],
                    "synthesized_answer": r[3],
                    "passages": json.loads(r[4]) if r[4] else [],
                    "claims": json.loads(r[5]) if r[5] else [],
                    "attachments": json.loads(r[6]) if r[6] else [],
                    "is_saved": bool(r[7]),
                    "created_at": str(r[8])
                })
    except Exception as e:
        logger.warning(f"Database get_user_activity_history error: {e}")
    return records


async def get_user_saved_chats_db(user_email: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Retrieve saved/bookmarked research chats for a user from Database."""
    active_engine = await check_and_get_working_engine()
    sql = text("""
        SELECT task_id, user_email, user_prompt, synthesized_answer, passages_json, claims_json, attachments_json, is_saved, created_at
        FROM aura_chat_history
        WHERE LOWER(user_email) = LOWER(:user_email) AND is_saved = 1
        ORDER BY created_at DESC
        LIMIT :limit;
    """)
    records = []
    try:
        async with active_engine.connect() as conn:
            result = await conn.execute(sql, {"user_email": user_email.lower().strip(), "limit": limit})
            rows = result.fetchall()
            for r in rows:
                records.append({
                    "task_id": r[0],
                    "user_email": r[1],
                    "user_prompt": r[2],
                    "synthesized_answer": r[3],
                    "passages": json.loads(r[4]) if r[4] else [],
                    "claims": json.loads(r[5]) if r[5] else [],
                    "attachments": json.loads(r[6]) if r[6] else [],
                    "is_saved": bool(r[7]),
                    "created_at": str(r[8])
                })
    except Exception as e:
        logger.warning(f"Database get_user_saved_chats error: {e}")
    return records
