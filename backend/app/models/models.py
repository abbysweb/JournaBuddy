"""
JournaBuddy SQLAlchemy ORM Models
Defines all database tables: tasks, document_chunks, provenance_log, journals.
Aligns with the schema specification in docs/planning/Plan.md §4.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Integer, Text, Boolean, Numeric,
    TIMESTAMP, ARRAY, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now_utc() -> datetime:
    """Returns current UTC timestamp for default column values."""
    return datetime.now(timezone.utc)


class Task(Base):
    """
    Task Orchestration Table.
    Created when a PDF is uploaded. Tracks end-to-end pipeline status.
    """
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    dashboard_payload: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=now_utc, onupdate=now_utc
    )

    # Relationships
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="task", cascade="all, delete-orphan"
    )
    provenance_entries: Mapped[list["ProvenanceLog"]] = relationship(
        "ProvenanceLog", back_populates="task", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """
    Semantic Document Chunks Table.
    Stores text segments with their 384-dimensional pgvector embeddings.
    """
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_name: Mapped[str] = mapped_column(String(100), nullable=True)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    # pgvector embedding stored as JSON list (real vector column managed by Alembic)
    embedding_json: Mapped[list] = mapped_column(JSONB, nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="chunks")


class ProvenanceLog(Base):
    """
    Provenance & Verifiability Log Table.
    Every metric the system produces is recorded here with formula, data source,
    confidence level, and raw input snapshot for full audit trails.
    """
    __tablename__ = "provenance_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    formula_used: Mapped[str] = mapped_column(Text, nullable=True)
    data_sources: Mapped[list] = mapped_column(ARRAY(Text), nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=True)
    raw_data_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=now_utc
    )

    task: Mapped["Task"] = relationship("Task", back_populates="provenance_entries")


class Journal(Base):
    """
    Journal Master Table.
    Populated by Phase 3 external enrichment (DOAJ, OpenAlex).
    Stores journal scope embeddings for cosine similarity matching.
    """
    __tablename__ = "journals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=True)
    is_doaj_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=True)
    # Scope embedding stored as JSON list (real vector column via Alembic)
    scope_embedding_json: Mapped[list] = mapped_column(JSONB, nullable=True)
