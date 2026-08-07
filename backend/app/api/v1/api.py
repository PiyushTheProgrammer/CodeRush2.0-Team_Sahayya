from fastapi import APIRouter
from app.api.v1.endpoints import research, payment, voice_attachment, auth_records
from app.api import research_router

api_router = APIRouter()
api_router.include_router(research.router, tags=["Research"])
api_router.include_router(research.router, prefix="/research", tags=["Research Tasks"])
api_router.include_router(research_router.router, prefix="/research-pipeline", tags=["Research Pipeline"])
api_router.include_router(payment.router, prefix="/payment", tags=["Payment"])
api_router.include_router(voice_attachment.router, tags=["Voice & Context Attachment"])
api_router.include_router(auth_records.router, tags=["Auth & Records Analytics"])


