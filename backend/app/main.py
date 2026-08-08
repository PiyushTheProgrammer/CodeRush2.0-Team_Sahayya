import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.api import research_router
from app.core.config import settings
from app.db.init_pgvector import init_pgvector
from app.db.init_users_db import init_users_table
from app.db.chat_history_db import init_chat_history_table
from app.db.attachments_db import init_attachments_table
from app.db.session import engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application database tables (aura_users, aura_chat_history, aura_attachments)...")
    try:
        await init_pgvector()
    except Exception as e:
        logger.warning(f"pgvector startup initialization notice: {e}")
    
    try:
        await init_users_table()
    except Exception as e:
        logger.warning(f"aura_users table initialization warning: {e}")

    try:
        await init_chat_history_table()
    except Exception as e:
        logger.warning(f"aura_chat_history table initialization warning: {e}")

    try:
        await init_attachments_table()
    except Exception as e:
        logger.warning(f"aura_attachments table initialization warning: {e}")

    yield
    logger.info("Disposing database connection pool...")
    await engine.dispose()





app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(research_router.router, prefix="/api/research", tags=["Research Package API"])



from app.db.session import check_and_get_working_engine, USING_SQLITE


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint verifying application status and DB connection."""
    db_status = "unknown"
    try:
        active_engine = await check_and_get_working_engine()
        async with active_engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
        db_status = "connected (SQLite fallback)" if USING_SQLITE else "connected (Supabase PostgreSQL)"
    except Exception as e:
        logger.error(f"Database health ping failed: {e}")
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
    }



# Mount frontend static directory and handle static CSS/JS routes
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/styles.css", include_in_schema=False)
    async def serve_css():
        return FileResponse(os.path.join(frontend_path, "styles.css"))

    @app.get("/app.js", include_in_schema=False)
    async def serve_js():
        return FileResponse(os.path.join(frontend_path, "app.js"))
