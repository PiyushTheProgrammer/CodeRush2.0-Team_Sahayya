import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def test_db():
    url = os.getenv("SUPABASE_DB_URL")
    print(f"Testing DB URL: {url}")
    try:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1;"))
            print("DB Connection SUCCESS:", res.scalar())
        await engine.dispose()
    except Exception as e:
        print("DB Connection FAILED:", type(e), e)

if __name__ == "__main__":
    asyncio.run(test_db())
