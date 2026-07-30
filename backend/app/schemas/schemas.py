"""
JournaBuddy Pydantic API Schemas
Defines request/response models for all API endpoints.
Ensures consistent, validated data contracts across the system.
"""
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response returned immediately after a PDF upload."""
    task_id: str = Field(..., description="Unique UUID for this analysis task")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    status: str = Field("queued", description="Initial task status")
    message: str = Field(..., description="Human-readable status message")


class TaskStatusResponse(BaseModel):
    """Full task status returned by GET /api/task/{task_id}."""
    task_id: str = Field(..., description="Unique UUID for this analysis task")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Current pipeline status")
    progress_percent: int = Field(..., description="Pipeline progress (0-100)")
    dashboard_payload: Optional[dict] = Field(
        None, description="Aggregated analysis results (populated as pipeline runs)"
    )
    created_at: str = Field(..., description="ISO 8601 timestamp of task creation")


class SymbolicCheckResult(BaseModel):
    """Results from the deterministic symbolic rule checker."""
    undefined_acronyms: list[str] = []
    defined_acronyms: dict[str, str] = {}
    missing_sections: list[str] = []
    found_sections: list[str] = []
    passive_voice_percent: float = 0.0
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    total_words: int = 0
    issues: list[str] = []


class JournalMatchResult(BaseModel):
    """Result of pgvector journal similarity matching."""
    journal_id: int
    title: str
    issn: str
    publisher: Optional[str]
    is_doaj_indexed: bool
    trust_score: Optional[float]
    compatibility_percent: float


class CrossrefResult(BaseModel):
    """Result of DOI verification against Crossref."""
    doi: str
    title: str
    journal: str
    publisher: str
    is_valid: bool


class OpenAlexResult(BaseModel):
    """Result of citation stats fetch from OpenAlex."""
    doi: str
    title: str
    citation_count: int
    concepts: list[str] = []



class AgentResult(BaseModel):
    """Result returned by a single LLM agent group."""
    agent_name: str
    status: str = "success"
    data: dict[str, Any] = {}
    provider_used: str = "Ollama"


class ProvenanceEntry(BaseModel):
    """Single provenance log record."""
    metric_name: str
    metric_value: dict[str, Any]
    formula_used: Optional[str] = None
    data_sources: list[str] = []
    confidence_level: str = "high"


class ErrorResponse(BaseModel):
    """Uniform error response schema for all API errors."""
    status: str = "error"
    error_code: str
    message: str
