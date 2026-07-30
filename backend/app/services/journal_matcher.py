"""
JournaBuddy Journal Matcher Service
Uses pgvector cosine distance to find the top journals whose scope most
closely matches the semantic embeddings of the manuscript.
"""
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class JournalMatcher:
    """Matches manuscripts to journals using pgvector."""

    def __init__(self, db: Session):
        self.db = db

    def find_matching_journals(self, task_id: uuid.UUID, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top K matching journals for a given task.
        
        Algorithm:
        1. Calculates the average embedding of all chunks for the task.
        2. Computes cosine distance (<=>) against the journals table.
        3. Returns the closest journals with a compatibility score.
        """
        query = text(
            """
            WITH manuscript_vector AS (
                SELECT AVG(embedding_json::text::vector) AS avg_emb
                FROM document_chunks
                WHERE task_id = :task_id
            )
            SELECT 
                j.id, 
                j.title, 
                j.issn,
                j.publisher,
                j.is_doaj_indexed,
                j.trust_score,
                -- Cosine distance (1 - distance = similarity)
                1 - (j.scope_embedding_json::text::vector <=> m.avg_emb) AS similarity_score
            FROM journals j, manuscript_vector m
            WHERE j.scope_embedding_json IS NOT NULL
            ORDER BY j.scope_embedding_json::text::vector <=> m.avg_emb ASC
            LIMIT :top_k;
            """
        )
        
        try:
            result = self.db.execute(query, {"task_id": str(task_id), "top_k": top_k}).fetchall()
            
            matches = []
            for row in result:
                matches.append({
                    "journal_id": row.id,
                    "title": row.title,
                    "issn": row.issn,
                    "publisher": row.publisher,
                    "is_doaj_indexed": row.is_doaj_indexed,
                    "trust_score": float(row.trust_score) if row.trust_score else None,
                    "compatibility_percent": round(float(row.similarity_score) * 100, 1),
                })
            
            logger.info(f"Found {len(matches)} matching journals for task {task_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Journal matching failed for task {task_id}: {e}")
            return []
