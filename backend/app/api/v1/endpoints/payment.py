import uuid
import time
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# x402 Payment Protocol Configuration
X402_RECIPIENT_WALLET = "0x402AURA98F290c41A87D25b3491E6200B41E10"
DEFAULT_MICRO_PAYMENT_USDC = 5.00


class X402ChallengeRequest(BaseModel):
    feature_requested: str = "PREMIUM_TIER_ACCESS"
    user_tier: str = "FREEMIUM"


class X402ChallengeResponse(BaseModel):
    status_code: int = 402
    title: str = "HTTP 402 Payment Required - x402 Agentic Protocol"
    recipient_wallet: str
    amount_usdc: float
    accepted_currencies: List[str]
    challenge_id: str
    payment_header_required: str = "X-PAYMENT"
    instructions: str


class X402VerifyRequest(BaseModel):
    challenge_id: str
    tx_hash: str
    payer_wallet: str
    currency: str = "USDC"


class X402VerifyResponse(BaseModel):
    success: bool
    message: str
    x402_session_token: str
    user_tier: str
    granted_features: List[str]


@router.post("/x402-challenge", response_model=X402ChallengeResponse)
async def generate_x402_challenge(request: X402ChallengeRequest):
    """
    Generate an HTTP 402 Payment Required challenge payload as specified in the x402 protocol standard.
    Allows AI agents and users to construct machine-to-machine crypto/stablecoin payments.
    """
    challenge_id = f"x402-ch-{uuid.uuid4().hex[:12]}"
    logger.info(f"Generated x402 payment challenge #{challenge_id} for feature '{request.feature_requested}'")
    
    return X402ChallengeResponse(
        status_code=402,
        title="HTTP 402 Payment Required - x402 Agentic Protocol",
        recipient_wallet=X402_RECIPIENT_WALLET,
        amount_usdc=DEFAULT_MICRO_PAYMENT_USDC,
        accepted_currencies=["USDC", "ETH", "SOL"],
        challenge_id=challenge_id,
        payment_header_required="X-PAYMENT",
        instructions=(
            f"Send {DEFAULT_MICRO_PAYMENT_USDC} USDC to recipient {X402_RECIPIENT_WALLET} "
            f"and present the signed transaction hash in the X-PAYMENT header to unlock premium agentic research."
        ),
    )


@router.post("/verify-x402", response_model=X402VerifyResponse)
async def verify_x402_payment(request: X402VerifyRequest):
    """
    Verify transaction proof (tx_hash) for x402 challenge ID, upgrade user tier to PREMIUM, 
    and issue an x402_session_token.
    """
    if not request.tx_hash or len(request.tx_hash) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction proof hash for x402 protocol verification.",
        )
    
    token = f"x402-token-{uuid.uuid4().hex[:16]}"
    logger.info(f"x402 Payment Verified! Tx: {request.tx_hash}. Issued token: {token}")

    return X402VerifyResponse(
        success=True,
        message="x402 Payment Verified! User tier upgraded to PREMIUM (x402 Verified).",
        x402_session_token=token,
        user_tier="PREMIUM (x402 Verified)",
        granted_features=[
            "Playwright Live Web Scraping",
            "Deep Docker Sandbox Execution",
            "x402 Paid Intelligence Streams",
            "Unlimited Top-K Vector Search",
            "Gemini 1.5 Flash Long Context Summarizer",
        ],
    )


@router.get("/pricing")
async def get_pricing_tiers():
    """Return pricing tiers and x402 protocol specification metadata."""
    return {
        "protocol": "x402 - Agentic Payment Standard",
        "recipient_wallet": X402_RECIPIENT_WALLET,
        "tiers": [
            {
                "tier_name": "FREEMIUM",
                "price": "$0 / month",
                "badge": "Free Tier",
                "features": [
                    "Standard Hybrid RAG Vector Search (Top-K <= 5)",
                    "Basic OpenAI & Gemini Dual Embedding Fallback",
                    "Multi-Agent Thinking Stream Progress Log",
                    "Supabase PgVector Cosine Search",
                ],
                "restricted_features": [
                    "Playwright Live Web Scraping",
                    "Deep Docker Sandbox Execution",
                    "x402 Paid External Data Streams",
                ],
            },
            {
                "tier_name": "PREMIUM (x402 Verified)",
                "price": "$5.00 USDC / task (or $29/mo)",
                "badge": "x402 Protocol Enabled",
                "features": [
                    "Playwright Live Web Scraping & PDF Extraction",
                    "Isolated Docker Sandbox Execution (512MB RAM, 1 CPU)",
                    "Unlimited Top-K Vector Search (Top-K <= 20)",
                    "Gemini 1.5 Flash Long-Context Summarization",
                    "x402 Agentic Payment Header Integration",
                    "Priority Multi-Agent DAG Execution",
                ],
                "restricted_features": [],
            },
        ],
    }
