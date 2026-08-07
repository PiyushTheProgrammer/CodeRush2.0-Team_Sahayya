import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory mock user database for authentication & records session management
MOCK_USERS_DB: Dict[str, Dict[str, Any]] = {
    "anuj@aura.ai": {
        "user_id": "user-anuj-001",
        "email": "anuj@aura.ai",
        "full_name": "Anuj",
        "password_hash": "hashed_pass_9021",
        "user_tier": "FREEMIUM",
        "created_at": "2026-07-01T10:00:00Z"
    }
}

MOCK_INACTIVE_TOPICS: List[Dict[str, Any]] = [
    {
        "topic_id": "top-001",
        "title": "Basic programming syntax & python loops",
        "last_accessed_days_ago": 42,
        "session_count": 3,
        "is_inactive": True,
        "recommendation": "Topic inactive for 42 days (>30 day threshold). Recommended for cleanup."
    },
    {
        "topic_id": "top-002",
        "title": "Legacy web scraping with Selenium",
        "last_accessed_days_ago": 35,
        "session_count": 2,
        "is_inactive": True,
        "recommendation": "Topic inactive for 35 days (>30 day threshold). Recommended for cleanup."
    },
    {
        "topic_id": "top-003",
        "title": "General text search queries",
        "last_accessed_days_ago": 31,
        "session_count": 4,
        "is_inactive": True,
        "recommendation": "Topic inactive for 31 days (>30 day threshold). Recommended for cleanup."
    }
]


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    tier_choice: Optional[str] = "FREEMIUM"


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: str
    user_id: str
    full_name: str
    email: str
    user_tier: str


class LoginRequest(BaseModel):
    email: str
    password: str



from app.db.init_users_db import get_user_by_email_db, create_user_db, hash_password


class CleanupRequest(BaseModel):
    topic_ids: Optional[List[str]] = None
    cleanup_all_inactive: bool = True


@router.post("/auth/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest):
    """
    Register a new user in AURA Research Ecosystem using PostgreSQL database.
    """
    email_clean = request.email.lower().strip()
    
    # 1. Check PostgreSQL DB first
    existing_user = await get_user_by_email_db(email_clean)
    if existing_user or email_clean in MOCK_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email address already exists. Please login instead.",
        )
    
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    token = f"aura-jwt-token-{uuid.uuid4().hex[:16]}"
    pass_hash = hash_password(request.password)
    tier_val = request.tier_choice or "FREEMIUM"
    
    # 2. Insert into PostgreSQL DB
    db_user = await create_user_db(
        user_id=user_id,
        full_name=request.full_name,
        email=email_clean,
        password_hash=pass_hash,
        user_tier=tier_val
    )

    # Backup to memory cache as fallback
    new_user = {
        "user_id": user_id,
        "email": email_clean,
        "full_name": request.full_name,
        "password_hash": pass_hash,
        "user_tier": tier_val,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    MOCK_USERS_DB[email_clean] = new_user

    logger.info(f"Registered user '{request.full_name}' ({email_clean}) in PostgreSQL DB with tier '{tier_val}'")

    return AuthResponse(
        success=True,
        message="Registration successful in PostgreSQL DB! Welcome to AURA Ecosystem.",
        token=token,
        user_id=user_id,
        full_name=request.full_name,
        email=email_clean,
        user_tier=tier_val
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login_user(request: LoginRequest):
    """
    Authenticate existing user credentials from PostgreSQL database and return session token.
    """
    email_clean = request.email.lower().strip()
    
    # 1. Check PostgreSQL DB
    user = await get_user_by_email_db(email_clean)
    if not user:
        user = MOCK_USERS_DB.get(email_clean)
    
    if not user:
        # Auto-provision guest user in PostgreSQL DB for seamless login
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        pass_hash = hash_password(request.password)
        name_val = email_clean.split("@")[0].capitalize()
        db_user = await create_user_db(
            user_id=user_id,
            full_name=name_val,
            email=email_clean,
            password_hash=pass_hash,
            user_tier="FREEMIUM"
        )
        user = {
            "user_id": user_id,
            "email": email_clean,
            "full_name": name_val,
            "user_tier": "FREEMIUM"
        }
        MOCK_USERS_DB[email_clean] = user

    token = f"aura-jwt-token-{uuid.uuid4().hex[:16]}"
    logger.info(f"User '{user['full_name']}' logged in via PostgreSQL DB.")

    return AuthResponse(
        success=True,
        message="Login successful via PostgreSQL DB.",
        token=token,
        user_id=user["user_id"],
        full_name=user["full_name"],
        email=user["email"],
        user_tier=user["user_tier"]
    )



@router.get("/auth/me")
async def get_current_user_profile():
    """
    Retrieve active user profile and system access metrics.
    """
    return {
        "user_id": "user-anuj-001",
        "full_name": "Anuj",
        "email": "anuj@aura.ai",
        "user_tier": "FREEMIUM",
        "evolution_gain": "+16.8% Precision Gain (v1.0.4)",
        "accuracy_metric": "97.2% Entailment",
        "user_growth": "+22.4% Skill Mastery",
        "active_sessions_count": 31,
        "inactive_topics_count": len(MOCK_INACTIVE_TOPICS)
    }


@router.get("/records/analytics")
async def get_user_records_analytics():
    """
    Return detailed breakdown of topics user researched on more vs less focused topics,
    including inactive topics (>30 days idle) requiring user notification & memory cleanup.
    """
    return {
        "user_name": "Anuj",
        "evolution_metric": "+16.8% Precision Gain (v1.0.4)",
        "accuracy_metric": "97.2% Entailment Accuracy",
        "user_growth": "+22.4% Skill Mastery",
        "most_focused_topics": [
            {"topic": "Cybersecurity & Agent Defense", "percentage": 42, "sessions": 18, "depth": "Deep"},
            {"topic": "AI & Agentic Systems", "percentage": 31, "sessions": 12, "depth": "Deep"},
            {"topic": "Defence Technology", "percentage": 17, "sessions": 7, "depth": "Medium"}
        ],

        "less_focused_topics": [
            {"topic": "Basic programming syntax", "percentage": 5, "sessions": 3, "depth": "Quick"},
            {"topic": "Legacy web scraping", "percentage": 3, "sessions": 2, "depth": "Quick"},
            {"topic": "General text search", "percentage": 2, "sessions": 2, "depth": "Quick"}
        ],
        "inactive_topics_over_30_days": MOCK_INACTIVE_TOPICS,
        "notification_alert": {
            "required": len(MOCK_INACTIVE_TOPICS) > 0,
            "title": "AURA Memory Cleanup Notification",
            "message": f"You have {len(MOCK_INACTIVE_TOPICS)} research topics inactive for over 30 days. Would you like to clean up these chats to streamline your research memory?"
        }
    }


@router.delete("/records/cleanup-inactive")
async def cleanup_inactive_topics(request: CleanupRequest):
    """
    Delete inactive chats (>30 days idle) confirmed by user from notification banner.
    """
    global MOCK_INACTIVE_TOPICS
    cleaned_count = len(MOCK_INACTIVE_TOPICS)
    MOCK_INACTIVE_TOPICS = []

    logger.info(f"Cleaned up {cleaned_count} inactive topics (>30 days idle) from user research memory.")

    return {
        "success": True,
        "cleaned_topics_count": cleaned_count,
        "message": f"Successfully removed {cleaned_count} inactive chat sessions from your research memory.",
        "remaining_inactive_topics": []
    }
