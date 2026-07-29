"""
JournaBuddy Embedding Service
Wraps sentence-transformers (all-MiniLM-L6-v2) as a singleton to generate
384-dimensional semantic embeddings for document chunks.
Stores embeddings to the document_chunks table via SQLAlchemy.
"""
import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.services.chunker import TextChunk

logger = logging.getLogger(__name__)

# Module-level singleton — loaded once to avoid repeated expensive I/O
_model = None


def _get_model():
    """
    Lazy-load the sentence-transformers model on first use.
    Uses all-MiniLM-L6-v2: 384 dimensions, fast inference, Apache 2.0 license.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


class EmbeddingService:
    """
    Generates 384-dimensional semantic embeddings and persists them to
    the document_chunks table in PostgreSQL (stored as JSONB lists).

    Usage:
        service = EmbeddingService()
        chunk_ids = service.embed_and_store(task_id, chunks, db_session)
    """

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of text strings.

        Args:
            texts: List of text strings to encode.

        Returns:
            List of 384-dim float vectors (one per input text).
        """
        model = _get_model()
        embeddings = model.encode(texts, batch_size=16, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def embed_and_store(
        self,
        task_id: uuid.UUID,
        chunks: list[TextChunk],
        db: Session,
    ) -> int:
        """
        Embed all chunks and persist them to the document_chunks table.

        Args:
            task_id: UUID of the parent task.
            chunks: List of TextChunk objects from SemanticChunker.
            db: SQLAlchemy synchronous session (used inside Celery worker).

        Returns:
            Number of chunks stored.
        """
        from app.models.models import DocumentChunk

        if not chunks:
            logger.warning(f"No chunks to embed for task {task_id}")
            return 0

        texts = [c.text for c in chunks]
        logger.info(f"Generating embeddings for {len(texts)} chunks (task={task_id})")

        embeddings = self.embed_texts(texts)

        # Persist each chunk with its embedding
        for chunk, embedding in zip(chunks, embeddings):
            db_chunk = DocumentChunk(
                task_id=task_id,
                chunk_index=chunk.index,
                section_name=chunk.section_name,
                text_content=chunk.text,
                embedding_json=embedding,  # Stored as JSONB list for portability
            )
            db.add(db_chunk)

        db.commit()
        logger.info(f"Stored {len(chunks)} chunks with embeddings for task {task_id}")
        return len(chunks)
