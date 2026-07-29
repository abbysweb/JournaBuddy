"""
Initial Database Schema Migration — Version 001
Creates all four core tables for JournaBuddy:
  - tasks
  - document_chunks
  - provenance_log
  - journals

Also activates the pgvector and uuid-ossp PostgreSQL extensions.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Alembic revision identifiers
revision: str = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the initial schema to the database."""

    # Enable required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ---------------------------------------------------------------
    # Table: tasks — tracks the lifecycle of each PDF analysis job
    # ---------------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("minio_object_key", sa.String(512), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("progress_percent", sa.Integer, server_default="0"),
        sa.Column("dashboard_payload", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # ---------------------------------------------------------------
    # Table: document_chunks — stores semantic text segments + vectors
    # ---------------------------------------------------------------
    op.create_table(
        "document_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("section_name", sa.String(100), nullable=True),
        sa.Column("text_content", sa.Text, nullable=False),
        sa.Column("embedding_json", postgresql.JSONB, nullable=True),
    )

    # Index for efficient task-based chunk retrieval
    op.create_index(
        "idx_document_chunks_task_id",
        "document_chunks",
        ["task_id"],
    )

    # ---------------------------------------------------------------
    # Table: provenance_log — full audit trail for every metric
    # ---------------------------------------------------------------
    op.create_table(
        "provenance_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", postgresql.JSONB, nullable=False),
        sa.Column("formula_used", sa.Text, nullable=True),
        sa.Column("data_sources", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("raw_data_snapshot", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Index for fast provenance lookup by task
    op.create_index(
        "idx_provenance_log_task_id",
        "provenance_log",
        ["task_id"],
    )

    # ---------------------------------------------------------------
    # Table: journals — master journal index for scope matching
    # ---------------------------------------------------------------
    op.create_table(
        "journals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("issn", sa.String(20), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("is_doaj_indexed", sa.Boolean, server_default="false"),
        sa.Column("trust_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("scope_embedding_json", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    """Revert the initial schema (drop all tables in dependency order)."""
    op.drop_table("journals")
    op.drop_index("idx_provenance_log_task_id", table_name="provenance_log")
    op.drop_table("provenance_log")
    op.drop_index("idx_document_chunks_task_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("tasks")
