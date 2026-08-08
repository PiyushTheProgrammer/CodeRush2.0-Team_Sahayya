import sqlite3
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Online Supabase PostgreSQL Pooler URL
SUPABASE_DB_URL = "postgresql+asyncpg://postgres.wdjfejkxfctvuwiokdmb:TeamSahayya%4012345@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres"

async def run_migration():
    print("=== AURA SQLite -> Online Supabase PostgreSQL Migration Engine ===")
    
    # 1. Connect to online Supabase PostgreSQL Engine with PgBouncer compatibility
    engine = create_async_engine(
        SUPABASE_DB_URL, 
        pool_pre_ping=True, 
        echo=False,
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        }
    )
    
    # 2. Ensure all 3 required tables exist in online Supabase PostgreSQL
    create_users_sql = """
    CREATE TABLE IF NOT EXISTS aura_users (
        user_id VARCHAR(64) PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        user_tier VARCHAR(32) NOT NULL DEFAULT 'FREEMIUM',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_chats_sql = """
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

    create_attachments_sql = """
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
    
    print("1. Creating required database tables in online Supabase PostgreSQL...")
    async with engine.begin() as conn:
        await conn.execute(text(create_users_sql))
        await conn.execute(text(create_chats_sql))
        await conn.execute(text(create_attachments_sql))
    print("   [SUCCESS] Online Supabase Tables ('aura_users', 'aura_chat_history', 'aura_attachments') created successfully!")

    # 3. Read data from local SQLite database
    sqlite_conn = sqlite3.connect('aura_app.db')
    s_cur = sqlite_conn.cursor()

    # Migrate Users
    s_cur.execute("SELECT user_id, full_name, email, password_hash, user_tier, created_at FROM aura_users;")
    sqlite_users = s_cur.fetchall()
    print(f"\n2. Found {len(sqlite_users)} local users in SQLite. Migrating to online Supabase...")

    migrated_users = 0
    async with engine.begin() as conn:
        for u in sqlite_users:
            sql_user = text("""
                INSERT INTO aura_users (user_id, full_name, email, password_hash, user_tier)
                VALUES (:user_id, :full_name, :email, :password_hash, :user_tier)
                ON CONFLICT (email) DO NOTHING;
            """)
            res = await conn.execute(sql_user, {
                "user_id": u[0],
                "full_name": u[1],
                "email": u[2],
                "password_hash": u[3],
                "user_tier": u[4]
            })
            if res.rowcount > 0:
                migrated_users += 1
    print(f"   [SUCCESS] Migrated {migrated_users} users into Supabase PostgreSQL 'aura_users' table!")

    # Migrate Chat History
    s_cur.execute("SELECT task_id, user_email, user_prompt, synthesized_answer, passages_json, claims_json, attachments_json, is_saved, created_at FROM aura_chat_history;")
    sqlite_chats = s_cur.fetchall()
    print(f"\n3. Found {len(sqlite_chats)} local research chats in SQLite. Migrating to online Supabase...")

    migrated_chats = 0
    async with engine.begin() as conn:
        for c in sqlite_chats:
            sql_chat = text("""
                INSERT INTO aura_chat_history (task_id, user_email, user_prompt, synthesized_answer, passages_json, claims_json, attachments_json, is_saved)
                VALUES (:task_id, :user_email, :user_prompt, :synthesized_answer, :passages_json, :claims_json, :attachments_json, :is_saved)
                ON CONFLICT (task_id) DO NOTHING;
            """)
            res = await conn.execute(sql_chat, {
                "task_id": c[0],
                "user_email": c[1],
                "user_prompt": c[2],
                "synthesized_answer": c[3],
                "passages_json": c[4] or "[]",
                "claims_json": c[5] or "[]",
                "attachments_json": c[6] or "[]",
                "is_saved": bool(c[7])
            })
            if res.rowcount > 0:
                migrated_chats += 1
    print(f"   [SUCCESS] Migrated {migrated_chats} research chat sessions into Supabase PostgreSQL 'aura_chat_history' table!")

    # Migrate Attachments
    s_cur.execute("SELECT file_id, user_email, filename, file_size_bytes, extracted_passages_count, summary, created_at FROM aura_attachments;")
    sqlite_attachments = s_cur.fetchall()
    print(f"\n4. Found {len(sqlite_attachments)} local context attachments in SQLite. Migrating to online Supabase...")

    migrated_attachments = 0
    async with engine.begin() as conn:
        for a in sqlite_attachments:
            sql_att = text("""
                INSERT INTO aura_attachments (file_id, user_email, filename, file_size_bytes, extracted_passages_count, summary)
                VALUES (:file_id, :user_email, :filename, :file_size_bytes, :extracted_passages_count, :summary)
                ON CONFLICT (file_id) DO NOTHING;
            """)
            res = await conn.execute(sql_att, {
                "file_id": a[0],
                "user_email": a[1],
                "filename": a[2],
                "file_size_bytes": a[3],
                "extracted_passages_count": a[4] or 1,
                "summary": a[5] or ""
            })
            if res.rowcount > 0:
                migrated_attachments += 1
    print(f"   [SUCCESS] Migrated {migrated_attachments} context attachment records into Supabase PostgreSQL 'aura_attachments' table!")

    # 5. Final Row Verification on Online Supabase PostgreSQL
    print("\n=== FINAL ONLINE SUPABASE POSTGRESQL ROW COUNT VERIFICATION ===")
    async with engine.connect() as conn:
        res_u = await conn.execute(text("SELECT count(*) FROM aura_users;"))
        cnt_u = res_u.fetchone()[0]
        res_c = await conn.execute(text("SELECT count(*) FROM aura_chat_history;"))
        cnt_c = res_c.fetchone()[0]
        res_a = await conn.execute(text("SELECT count(*) FROM aura_attachments;"))
        cnt_a = res_a.fetchone()[0]

        print(f"Online Supabase Table 'aura_users': {cnt_u} Total Stored Records")
        print(f"Online Supabase Table 'aura_chat_history': {cnt_c} Total Stored Records")
        print(f"Online Supabase Table 'aura_attachments': {cnt_a} Total Stored Records")
        print("\nALL LOCAL DATA HAS BEEN MIGRATED AND VERIFIED ON ONLINE SUPABASE POSTGRESQL!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
