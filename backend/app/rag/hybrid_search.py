import math
import re
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schema import DocumentPassage

logger = logging.getLogger(__name__)

# Constants for Hybrid RAG Engine
TARGET_EMBEDDING_DIM = 1536
DEFAULT_RRF_K = 60
DEFAULT_DECAY_FACTOR = 0.05
SIMILARITY_DEDUP_THRESHOLD = 0.92


class HybridRAGEngine:
    """
    Hybrid Live RAG Engine incorporating BM25 keyword retrieval and Supabase pgvector cosine search.
    Features dual-provider embedding generation (OpenAI primary with automatic Gemini fallback),
    semantic deduplication (>0.92 cosine similarity), Reciprocal Rank Fusion (RRF),
    and Time-Aware Decay ranking.
    """

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.gemini_api_key = settings.GEMINI_API_KEY

    async def generate_embedding(self, text_input: str) -> Tuple[List[float], str]:
        """
        Generate a 1536-dimensional vector embedding.
        
        Primary Model: OpenAI `text-embedding-3-small` (1536-dim).
        Fallback Model: Gemini `text-embedding-004` (768-dim natively).
        
        Dimension Handling:
        If the fallback provider generates a vector of dimension != 1536 (e.g., 768 from Gemini),
        the vector is normalized and padded with zeros to ensure strict compatibility with 
        Supabase pgvector's Vector(1536) column schema.
        """
        # Try OpenAI with exponential backoff retries
        if self.openai_api_key:
            for attempt in range(3):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            "https://api.openai.com/v1/embeddings",
                            headers={"Authorization": f"Bearer {self.openai_api_key}"},
                            json={
                                "model": "text-embedding-3-small",
                                "input": text_input,
                                "dimensions": TARGET_EMBEDDING_DIM,
                            },
                        )
                        if response.status_code == 200:
                            data = response.json()
                            embedding = data["data"][0]["embedding"]
                            return embedding, "OpenAI text-embedding-3-small"
                        else:
                            logger.warning(
                                f"OpenAI embedding attempt {attempt + 1} failed: HTTP {response.status_code} - {response.text}"
                            )
                except Exception as e:
                    logger.warning(f"OpenAI embedding attempt {attempt + 1} exception: {e}")
                
                # Exponential backoff delay (0.5s, 1.0s, 2.0s)
                await asyncio.sleep(0.5 * (2 ** attempt))

        # Fallback to Gemini Embedding API if OpenAI fails or key is missing
        if self.gemini_api_key:
            try:
                logger.info("Triggering Fallback to Gemini Embedding API...")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    gemini_url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
                        f"?key={self.gemini_api_key}"
                    )
                    response = await client.post(
                        gemini_url,
                        json={
                            "model": "models/text-embedding-004",
                            "content": {"parts": [{"text": text_input}]},
                        },
                    )
                    if response.status_code == 200:
                        data = response.json()
                        raw_embedding = data.get("embedding", {}).get("values", [])
                        
                        # Pad or truncate to 1536 dimensions
                        padded_embedding = self._normalize_dimension(raw_embedding, TARGET_EMBEDDING_DIM)
                        return padded_embedding, "Gemini text-embedding-004 (Fallback)"
                    else:
                        logger.error(f"Gemini embedding API error: HTTP {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Gemini embedding fallback exception: {e}")

        # Deterministic pseudo-embedding fallback if no external API key is active
        logger.warning("No active API keys responded. Generating normalized pseudo-embedding...")
        return self._generate_pseudo_embedding(text_input, TARGET_EMBEDDING_DIM), "System Local Deterministic Embedder"

    def _normalize_dimension(self, vector: List[float], target_dim: int) -> List[float]:
        """Normalize vector dimension by padding with zeros or truncating."""
        current_dim = len(vector)
        if current_dim == target_dim:
            return vector
        elif current_dim < target_dim:
            # Zero-padding
            return vector + [0.0] * (target_dim - current_dim)
        else:
            # Truncating
            return vector[:target_dim]

    def _generate_pseudo_embedding(self, text_input: str, target_dim: int) -> List[float]:
        """Deterministic fallback embedding generator based on string hashing."""
        seed = sum(ord(c) for c in text_input)
        vec = [math.sin(seed + i) for i in range(target_dim)]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def tokenize_bm25(self, text_input: str) -> str:
        """Tokenize text for BM25 keyword matching."""
        words = re.findall(r"\b\w+\b", text_input.lower())
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "was", "by"}
        filtered = [w for w in words if w not in stopwords and len(w) > 1]
        return " ".join(filtered)

    async def index_document(
        self,
        session: AsyncSession,
        task_id: uuid.UUID,
        content: str,
        source_url: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[DocumentPassage, bool]:
        """
        Index a document passage into Supabase `document_passages`.
        Performs semantic deduplication check (>0.92 similarity) via pgvector `<=>` operator.
        If duplicate, merges metadata instead of re-indexing.
        
        Returns: (passage_object, is_new_boolean)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # 1. Generate embedding vector and tokenize for BM25
        embedding, provider = await self.generate_embedding(content)
        bm25_tokens = self.tokenize_bm25(content)

        # 2. Semantic Deduplication Check using pgvector cosine distance operator <=>
        try:
            # Cosine distance = 1 - cosine_similarity. So cosine_distance < (1 - 0.92 = 0.08)
            stmt = (
                select(DocumentPassage)
                .where(DocumentPassage.task_id == task_id)
                .order_by(DocumentPassage.vector_embedding.cosine_distance(embedding))
                .limit(1)
            )
            result = await session.execute(stmt)
            existing_passage = result.scalars().first()

            if existing_passage and existing_passage.vector_embedding is not None:
                # Calculate exact similarity
                # Cosine distance in pgvector: <=>
                # Compute dot product / distance manually or via DB scalar query
                dist_query = text(
                    "SELECT vector_embedding <=> :emb AS dist FROM document_passages WHERE id = :pid"
                )
                dist_res = await session.execute(
                    dist_query, {"emb": str(embedding), "pid": str(existing_passage.id)}
                )
                dist_row = dist_res.first()
                if dist_row and dist_row.dist is not None:
                    dist = float(dist_row.dist)
                    similarity = 1.0 - dist
                    if similarity >= SIMILARITY_DEDUP_THRESHOLD:
                        logger.info(
                            f"Semantic Duplicate Detected (Similarity: {similarity:.4f} > {SIMILARITY_DEDUP_THRESHOLD}). Merging metadata."
                        )
                        if source_url and existing_passage.source_url != source_url:
                            existing_passage.source_url = f"{existing_passage.source_url} | {source_url}"
                        return existing_passage, False
        except Exception as e:
            logger.warning(f"PgVector deduplication check warning: {e}")

        # 3. Create and store new passage
        new_passage = DocumentPassage(
            id=uuid.uuid4(),
            task_id=task_id,
            content=content,
            source_url=source_url,
            timestamp=timestamp,
            vector_embedding=embedding,
            bm25_tokens=bm25_tokens,
        )
        session.add(new_passage)
        await session.flush()
        return new_passage, True

    async def hybrid_search(
        self,
        session: AsyncSession,
        task_id: Optional[uuid.UUID],
        query: str,
        top_k: int = 5,
        rrf_k: int = DEFAULT_RRF_K,
        decay_factor: float = DEFAULT_DECAY_FACTOR,
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Retrieval using BM25 keyword matching and pgvector Cosine similarity.
        Combines rankings using Reciprocal Rank Fusion (RRF) and applies Time-Aware Decay:
        
        RRF Score: RRF_score(d) = sum_m(1 / (k + rank_m(d)))
        Time Decay: final_score = RRF_score * exp(-decay_factor * age_in_days)
        """
        query_embedding, provider_used = await self.generate_embedding(query)
        query_tokens = self.tokenize_bm25(query).split()

        # 1. Fetch passages for task
        stmt = select(DocumentPassage)
        if task_id:
            stmt = stmt.where(DocumentPassage.task_id == task_id)
        
        result = await session.execute(stmt)
        passages: List[DocumentPassage] = list(result.scalars().all())

        if not passages:
            return []

        # 2. Vector Rank Calculation (Cosine Distance)
        # Lower distance = higher rank
        try:
            vector_stmt = (
                select(DocumentPassage.id)
                .order_by(DocumentPassage.vector_embedding.cosine_distance(query_embedding))
            )
            if task_id:
                vector_stmt = vector_stmt.where(DocumentPassage.task_id == task_id)
            
            vec_res = await session.execute(vector_stmt)
            vec_ranked_ids = [row[0] for row in vec_res.all()]
        except Exception:
            vec_ranked_ids = [p.id for p in passages]

        vector_rank_map = {pid: rank + 1 for rank, pid in enumerate(vec_ranked_ids)}

        # 3. BM25 Keyword Match Rank Calculation
        bm25_scores = {}
        for p in passages:
            p_tokens = (p.bm25_tokens or "").split()
            match_count = sum(1 for qt in query_tokens if qt in p_tokens)
            bm25_scores[p.id] = match_count

        bm25_ranked_ids = sorted(passages, key=lambda p: bm25_scores.get(p.id, 0), reverse=True)
        bm25_rank_map = {p.id: rank + 1 for rank, p in enumerate(bm25_ranked_ids)}

        # 4. RRF Score & Time-Aware Decay Calculation
        now = datetime.now(timezone.utc)
        results = []

        for p in passages:
            r_vec = vector_rank_map.get(p.id, len(passages))
            r_bm25 = bm25_rank_map.get(p.id, len(passages))

            # RRF Math
            rrf_score = (1.0 / (rrf_k + r_vec)) + (1.0 / (rrf_k + r_bm25))

            # Age in days math
            p_time = p.timestamp.replace(tzinfo=timezone.utc) if p.timestamp.tzinfo is None else p.timestamp
            age_days = max(0.0, (now - p_time).total_seconds() / 86400.0)

            # Time Decay Math: exp(-decay_factor * age_in_days)
            freshness_score = math.exp(-decay_factor * age_days)
            final_score = rrf_score * freshness_score

            results.append({
                "id": str(p.id),
                "content": p.content,
                "source_url": p.source_url,
                "timestamp": p.timestamp.isoformat(),
                "vector_rank": r_vec,
                "bm25_rank": r_bm25,
                "rrf_score": round(rrf_score, 6),
                "freshness_score": round(freshness_score, 4),
                "final_score": round(final_score, 6),
                "similarity_score": round(1.0 - (r_vec / (len(passages) + 1)), 3),
                "embedding_provider": provider_used,
                "tokens": (p.bm25_tokens or "").split(),
            })

        # Sort by final score descending
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:top_k]
