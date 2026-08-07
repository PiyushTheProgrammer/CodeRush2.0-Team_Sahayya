import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.db.chat_history_db import (
    get_user_activity_history_db,
    get_user_saved_chats_db,
    toggle_save_chat_db,
    save_chat_session_db
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ToggleSaveChatRequest(BaseModel):
    task_id: str
    is_saved: bool = True
    user_email: Optional[str] = "anuj@aura.ai"
    user_prompt: Optional[str] = None
    synthesized_answer: Optional[str] = None


class ToggleSaveChatResponse(BaseModel):
    success: bool
    task_id: str
    is_saved: bool
    message: str


@router.get("/activity", response_model=List[Dict[str, Any]])
async def get_user_activity_history(email: str = Query("anuj@aura.ai")):
    """
    Fetch user's recent research activity history from Supabase PostgreSQL aura_chat_history table.
    """
    records = await get_user_activity_history_db(user_email=email)
    logger.info(f"Retrieved {len(records)} activity history records for user {email}")
    return records


@router.get("/saved", response_model=List[Dict[str, Any]])
async def get_user_saved_chats(email: str = Query("anuj@aura.ai")):
    """
    Fetch user's bookmarked/saved research chats from Supabase PostgreSQL aura_chat_history table.
    Saved chats are rendered when the user clicks on the RESEARCH tab in the left sidebar.
    """
    records = await get_user_saved_chats_db(user_email=email)
    logger.info(f"Retrieved {len(records)} saved research chats for user {email}")
    return records


@router.post("/save", response_model=ToggleSaveChatResponse)
async def toggle_save_chat_endpoint(request: ToggleSaveChatRequest):
    """
    Bookmark or un-bookmark an important research chat in Supabase PostgreSQL aura_chat_history table.
    """
    if request.user_prompt and request.synthesized_answer:
        await save_chat_session_db(
            task_id=request.task_id,
            user_email=request.user_email or "anuj@aura.ai",
            user_prompt=request.user_prompt,
            synthesized_answer=request.synthesized_answer,
            is_saved=request.is_saved
        )
    
    success = await toggle_save_chat_db(task_id=request.task_id, is_saved=request.is_saved)
    status_str = "saved to Research bookmarks" if request.is_saved else "removed from Research bookmarks"
    
    return ToggleSaveChatResponse(
        success=True,
        task_id=request.task_id,
        is_saved=request.is_saved,
        message=f"Research session #{request.task_id[:8]} successfully {status_str} in Supabase PostgreSQL."
    )
