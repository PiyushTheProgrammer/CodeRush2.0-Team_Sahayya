import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.init_users_db import init_users_table, create_user_db, get_user_by_email_db, hash_password
from app.db.chat_history_db import init_chat_history_table, save_chat_session_db, get_user_saved_chats_db
from app.db.attachments_db import init_attachments_table, save_attachment_db

async def run_test():
    print("Testing DB initialization...")
    await init_users_table()
    await init_chat_history_table()
    await init_attachments_table()
    print("Tables initialized successfully!")

    # Test user creation
    user = await create_user_db("user-test-1", "Sahayya Tester", "testuser@aura.ai", hash_password("secret123"), "FREEMIUM")
    print("User Created in DB:", user)

    # Test query user
    queried = await get_user_by_email_db("testuser@aura.ai")
    print("Queried User from DB:", queried)

    # Test chat saving
    saved_chat = await save_chat_session_db(
        task_id="task-test-88",
        user_email="testuser@aura.ai",
        user_prompt="Test prompt query",
        synthesized_answer="Test synthesized answer report",
        passages_json="[]",
        claims_json="[]",
        attachments_json="[{\"name\": \"test.pdf\", \"size\": 1024}]",
        is_saved=True
    )
    print("Saved Chat Session in DB:", saved_chat)

    # Test retrieved saved chats
    saved_list = await get_user_saved_chats_db("testuser@aura.ai")
    print("Retrieved Saved Chats:", len(saved_list), saved_list)

    # Test attachment saving
    att = await save_attachment_db("file-test-1", "testuser@aura.ai", "sample.pdf", 2048, 5, "Sample summary")
    print("Saved Attachment in DB:", att)

if __name__ == "__main__":
    asyncio.run(run_test())
