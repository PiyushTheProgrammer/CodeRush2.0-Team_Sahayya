from fastapi import APIRouter
from app.api.v1.endpoints import research, payment

api_router = APIRouter()
api_router.include_router(research.router, tags=["Research"])
api_router.include_router(research.router, prefix="/research", tags=["Research"])
api_router.include_router(payment.router, prefix="/payment", tags=["Payment"])
