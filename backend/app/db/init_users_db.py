import logging
import hashlib
from typing import Optional, Dict, Any
from sqlalchemy import text
from app.db.session import engine

logger = logging.getLogger(__name__)

async def init_users_table() -> None:
    """Ensure aura_users table exists in PostgreSQL / Supabase on application startup."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS aura_users (
        user_id VARCHAR(64) PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        user_tier VARCHAR(32) NOT NULL DEFAULT 'FREEMIUM',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text(create_table_sql))
        logger.info("PostgreSQL 'aura_users' table initialized successfully.")
    except Exception as e:
        logger.warning(f"PostgreSQL users table initialization notice: {e}")

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

async def get_user_by_email_db(email: str) -> Optional[Dict[str, Any]]:
    """Query user from PostgreSQL aura_users table by email."""
    sql = text("SELECT user_id, full_name, email, password_hash, user_tier, created_at FROM aura_users WHERE LOWER(email) = LOWER(:email) LIMIT 1;")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(sql, {"email": email.lower().strip()})
            row = result.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "full_name": row[1],
                    "email": row[2],
                    "password_hash": row[3],
                    "user_tier": row[4],
                    "created_at": str(row[5])
                }
    except Exception as e:
        logger.warning(f"Database query user error: {e}")
    return None

async def create_user_db(user_id: str, full_name: str, email: str, password_hash: str, user_tier: str = "FREEMIUM") -> Optional[Dict[str, Any]]:
    """Insert new registered user into PostgreSQL aura_users table."""
    sql = text("""
        INSERT INTO aura_users (user_id, full_name, email, password_hash, user_tier)
        VALUES (:user_id, :full_name, :email, :password_hash, :user_tier)
        RETURNING user_id, full_name, email, user_tier, created_at;
    """)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(sql, {
                "user_id": user_id,
                "full_name": full_name,
                "email": email.lower().strip(),
                "password_hash": password_hash,
                "user_tier": user_tier
            })
            row = result.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "full_name": row[1],
                    "email": row[2],
                    "user_tier": row[3],
                    "created_at": str(row[4])
                }
    except Exception as e:
        logger.warning(f"Database insert user error: {e}")
    return None
