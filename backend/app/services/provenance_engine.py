"""
JournaBuddy ProvenanceEngine Service
Records every metric produced by the analysis pipeline into the provenance_log
table, providing a full audit trail of how each score was derived.

Each provenance entry captures:
  - metric_name: Human-readable label (e.g., "flesch_reading_ease")
  - metric_value: The computed result (JSONB)
  - formula_used: Textual description of the formula or method
  - data_sources: List of services/models that produced the data
  - confidence_level: "high" / "medium" / "low" / "degraded"
  - raw_data_snapshot: Input data used to compute the metric
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProvenanceEngine:
    """
    Writes verifiable audit entries to the provenance_log table.

    Every call to log() creates one database row capturing:
    - What metric was produced
    - What formula or algorithm was used
    - What data sources were consulted
    - The raw input data used to produce the result

    This ensures every score in JournaBuddy is fully explainable and verifiable.
    """

    def __init__(self, task_id: uuid.UUID, db: Session):
        """
        Args:
            task_id: UUID of the analysis task this provenance belongs to.
            db: Synchronous SQLAlchemy session (used inside Celery workers).
        """
        self.task_id = task_id
        self.db = db

    def log(
        self,
        metric_name: str,
        metric_value: Any,
        formula_used: Optional[str] = None,
        data_sources: Optional[list[str]] = None,
        confidence_level: str = "high",
        raw_data_snapshot: Optional[dict] = None,
    ) -> None:
        """
        Record a single metric in the provenance_log table.

        Args:
            metric_name: Short identifier for the metric (e.g., "passive_voice_percent").
            metric_value: The computed result. Will be stored as JSONB.
            formula_used: Human-readable formula or algorithm description.
            data_sources: List of services/libraries that produced the data.
            confidence_level: "high", "medium", "low", or "degraded".
            raw_data_snapshot: Optional dict of raw input data for full reproducibility.
        """
        from app.models.models import ProvenanceLog

        # Normalise metric_value to a JSON-serialisable dict
        if not isinstance(metric_value, dict):
            metric_value = {"value": metric_value}

        entry = ProvenanceLog(
            task_id=self.task_id,
            metric_name=metric_name,
            metric_value=metric_value,
            formula_used=formula_used,
            data_sources=data_sources or [],
            confidence_level=confidence_level,
            raw_data_snapshot=raw_data_snapshot or {},
            created_at=datetime.now(timezone.utc),
        )

        try:
            self.db.add(entry)
            self.db.flush()  # Write to DB without committing the full transaction
            logger.debug(
                f"Provenance recorded — task={self.task_id} metric={metric_name} "
                f"confidence={confidence_level}"
            )
        except Exception as e:
            logger.error(f"Failed to write provenance for {metric_name}: {e}")
            # Don't raise — provenance failure should never block the main pipeline

    def log_symbolic_checks(self, symbolic_result) -> None:
        """
        Log all outputs from the SymbolicChecker in one call.

        Args:
            symbolic_result: SymbolicCheckResult dataclass instance.
        """
        self.log(
            metric_name="flesch_reading_ease",
            metric_value={"value": symbolic_result.flesch_reading_ease},
            formula_used=(
                "Flesch Reading Ease = 206.835 "
                "- 1.015 × (total_words / total_sentences) "
                "- 84.6 × (total_syllables / total_words)"
            ),
            data_sources=["textstat==0.7.3"],
            confidence_level="high",
            raw_data_snapshot={"total_words": symbolic_result.total_words},
        )

        self.log(
            metric_name="flesch_kincaid_grade",
            metric_value={"value": symbolic_result.flesch_kincaid_grade},
            formula_used=(
                "Flesch-Kincaid Grade = 0.39 × (total_words / total_sentences) "
                "+ 11.8 × (total_syllables / total_words) - 15.59"
            ),
            data_sources=["textstat==0.7.3"],
            confidence_level="high",
            raw_data_snapshot={"total_words": symbolic_result.total_words},
        )

        self.log(
            metric_name="passive_voice_density",
            metric_value={"percent": symbolic_result.passive_voice_percent},
            formula_used=(
                "passive_voice_density = "
                "(passive_voice_sentences / total_sentences) × 100"
            ),
            data_sources=["regex pattern: is|was|were|are|been + past participle"],
            confidence_level="medium",
        )

        self.log(
            metric_name="acronym_check",
            metric_value={
                "undefined_count": len(symbolic_result.undefined_acronyms),
                "undefined": symbolic_result.undefined_acronyms[:20],
                "defined_count": len(symbolic_result.defined_acronyms),
            },
            formula_used="Regex scan: full form (ACRONYM) pattern matching",
            data_sources=["regex"],
            confidence_level="high",
        )

        self.log(
            metric_name="section_completeness",
            metric_value={
                "found": list(symbolic_result.found_sections),
                "missing": list(symbolic_result.missing_sections),
                "completeness_percent": round(
                    len(symbolic_result.found_sections)
                    / max(len(symbolic_result.found_sections | symbolic_result.missing_sections), 1)
                    * 100,
                    1,
                ),
            },
            formula_used="Pattern matching against required academic section list",
            data_sources=["symbolic_checker"],
            confidence_level="high",
        )

    def log_agent_result(
        self,
        agent_name: str,
        result: dict,
        provider_used: str = "Ollama",
    ) -> None:
        """
        Log the output of a single LLM agent run.

        Args:
            agent_name: Name of the agent group (e.g., "Group A - Document Intelligence").
            result: Parsed JSON result dict from the agent.
            provider_used: LLM provider that produced the result.
        """
        confidence = "degraded" if result.get("status") == "degraded" else "medium"

        self.log(
            metric_name=f"agent_{agent_name.lower().replace(' ', '_')}",
            metric_value=result,
            formula_used=f"Structured JSON prompt via {provider_used} LLM inference",
            data_sources=[provider_used, f"model={result.get('model', 'unknown')}"],
            confidence_level=confidence,
            raw_data_snapshot={"agent": agent_name, "provider": provider_used},
        )
