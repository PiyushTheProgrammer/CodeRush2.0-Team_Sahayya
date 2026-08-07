import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    passages: Mapped[List["DocumentPassage"]] = relationship(
        "DocumentPassage", back_populates="task", cascade="all, delete-orphan"
    )
    claims: Mapped[List["ClaimNode"]] = relationship(
        "ClaimNode", back_populates="task", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="task", cascade="all, delete-orphan"
    )


class DocumentPassage(Base):
    __tablename__ = "document_passages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Vector dimension 1536 tailored for OpenAI text-embedding-3-small
    vector_embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536), nullable=True)
    bm25_tokens: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    task: Mapped["ResearchTask"] = relationship("ResearchTask", back_populates="passages")
    evidence_links: Mapped[List["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="passage", cascade="all, delete-orphan"
    )


class ClaimNode(Base):
    __tablename__ = "claim_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_interpretation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    task: Mapped["ResearchTask"] = relationship("ResearchTask", back_populates="claims")
    evidence_links: Mapped[List["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="claim", cascade="all, delete-orphan"
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_nodes.id", ondelete="CASCADE"), nullable=False
    )
    passage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_passages.id", ondelete="CASCADE"), nullable=False
    )
    transformation_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    claim: Mapped["ClaimNode"] = relationship("ClaimNode", back_populates="evidence_links")
    passage: Mapped["DocumentPassage"] = relationship("DocumentPassage", back_populates="evidence_links")


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    strategy_code: Mapped[str] = mapped_column(Text, nullable=False)
    performance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by_governance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    task: Mapped[Optional["ResearchTask"]] = relationship("ResearchTask", back_populates="audit_logs")
