import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class PlagiarismChecker:
    """Checks manuscript chunks against the internal database for plagiarism using pgvector."""

    def __init__(self, db: Session):
        self.db = db

    def check_for_plagiarism(self, task_id: uuid.UUID, similarity_threshold: float = 0.90) -> list[dict[str, Any]]:
        """
        Cross-references every chunk of the given task against all other chunks in the database.
        Returns exact sentences that match above the threshold, citing the source filename.
        """
        logger.info(f"Running Plagiarism Check for task {task_id}")
        
        # We use a LATERAL JOIN to find the single closest chunk from ANY OTHER task for each chunk in our task.
        query = text(
            """
            WITH current_chunks AS (
                SELECT id, text_content, embedding_json::text::vector AS emb
                FROM document_chunks
                WHERE task_id = :task_id AND embedding_json IS NOT NULL
            )
            SELECT 
                c.text_content AS original_text,
                other.text_content AS plagiarized_text,
                t.filename AS source_filename,
                1 - (c.emb <=> other.embedding_json::text::vector) AS similarity_score
            FROM current_chunks c
            CROSS JOIN LATERAL (
                SELECT text_content, task_id, embedding_json
                FROM document_chunks dc
                WHERE dc.task_id != :task_id AND dc.embedding_json IS NOT NULL
                ORDER BY c.emb <=> dc.embedding_json::text::vector ASC
                LIMIT 1
            ) other
            JOIN tasks t ON other.task_id = t.id
            WHERE 1 - (c.emb <=> other.embedding_json::text::vector) >= :threshold
            ORDER BY similarity_score DESC
            LIMIT 10; -- Cap to top 10 violations to avoid huge payloads
            """
        )
        
        try:
            result = self.db.execute(query, {
                "task_id": str(task_id),
                "threshold": similarity_threshold
            }).fetchall()
            
            violations = []
            for row in result:
                violations.append({
                    "original_text": row.original_text,
                    "plagiarized_text": row.plagiarized_text,
                    "source_filename": row.source_filename,
                    "similarity_score": round(float(row.similarity_score) * 100, 2)
                })
                
            if violations:
                logger.warning(f"PLAGIARISM DETECTED for task {task_id}: {len(violations)} violations found!")
                
            return violations
            
        except Exception as e:
            logger.error(f"Plagiarism check failed for task {task_id}: {e}")
            return []
