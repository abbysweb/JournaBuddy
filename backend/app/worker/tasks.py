"""
JournaBuddy Celery Task Definitions
Defines two main task flows routed to the correct worker pools:

  extract_pdf_task  → io_bound queue
    1. Download PDF from MinIO
    2. Extract text via pdfplumber
    3. Chunk text into semantic sections
    4. Generate sentence-transformer embeddings
    5. Persist chunks to document_chunks table
    6. Run symbolic rule checks (acronym, sections, readability)
    7. Log all metrics to provenance_log
    8. Dispatch run_agent_task for each LLM agent group

  run_agent_task    → llm_bound queue
    1. Send structured JSON prompt to OllamaAgent (with cascade fallback)
    2. Parse and validate JSON response
    3. Update task dashboard_payload with agent results
    4. Log agent output to provenance_log
"""
import io
import logging
import uuid
import asyncio
import re
from typing import Any

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.worker.celery_app import celery_app
from app.services.crossref import CrossrefClient
from app.services.openalex import OpenAlexClient
from app.services.journal_matcher import JournalMatcher
from celery import chord

logger = logging.getLogger(__name__)

# LLM agent group definitions: name + prompt template + expected response schema
AGENT_GROUPS = [
    {
        "name": "document_intelligence",
        "label": "Group A – Document Intelligence",
        "prompt_template": (
            "Analyse this academic manuscript excerpt and extract key metadata.\n\n"
            "Text:\n{text}\n\n"
            "Return a JSON object with: title (string), authors (list), "
            "keywords (list of 5-10), domain (string), abstract_quality_score (0-10)."
        ),
        "schema": {
            "title": "string",
            "authors": ["string"],
            "keywords": ["string"],
            "domain": "string",
            "abstract_quality_score": "number (0-10)",
        },
    },
    {
        "name": "language_compliance",
        "label": "Group B – Language & Compliance",
        "prompt_template": (
            "Evaluate the academic tone and language compliance of this text.\n\n"
            "Text:\n{text}\n\n"
            "Return a JSON object with: tone_score (0-10), formality_score (0-10), "
            "academic_voice_score (0-10), top_issues (list of strings)."
        ),
        "schema": {
            "tone_score": "number (0-10)",
            "formality_score": "number (0-10)",
            "academic_voice_score": "number (0-10)",
            "top_issues": ["string"],
        },
    },
    {
        "name": "research_rigor",
        "label": "Group D – Research Rigor",
        "prompt_template": (
            "Evaluate the research rigor and methodological completeness of this text.\n\n"
            "Text:\n{text}\n\n"
            "Return a JSON object with: methodology_score (0-10), "
            "dataset_declaration_present (bool), statistical_validity_score (0-10), "
            "improvement_suggestions (list of strings)."
        ),
        "schema": {
            "methodology_score": "number (0-10)",
            "dataset_declaration_present": "boolean",
            "statistical_validity_score": "number (0-10)",
            "improvement_suggestions": ["string"],
        },
    },
]


def _get_sync_db():
    """
    Create a synchronous SQLAlchemy session for use inside Celery workers.
    Celery tasks are synchronous; asyncpg cannot be used here.
    Uses psycopg2 driver instead of asyncpg.
    """
    sync_url = settings.database_url.replace(
        "postgresql+asyncpg", "postgresql+psycopg2"
    )
    engine = create_engine(sync_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _get_minio_client():
    """Create and return a boto3 S3 client pointing to MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
    )


@celery_app.task(bind=True, name="app.worker.tasks.extract_pdf_task", max_retries=3)
def extract_pdf_task(self, task_id: str, object_key: str) -> dict:
    """
    io_bound worker: Full PDF intelligence extraction pipeline.

    Steps:
        1. Download PDF bytes from MinIO
        2. Extract text via pdfplumber
        3. Chunk into semantic sections
        4. Generate sentence-transformer embeddings
        5. Persist chunks to DB
        6. Run symbolic checks
        7. Log provenance entries
        8. Dispatch LLM agent tasks

    Args:
        task_id: UUID string for the analysis task.
        object_key: MinIO object key of the uploaded PDF.

    Returns:
        Summary dict with chunk count, agent task IDs, and symbolic check results.
    """
    from app.models.models import Task
    from app.services.pdf_extractor import extract_text_from_pdf
    from app.services.chunker import SemanticChunker
    from app.services.embedding_service import EmbeddingService
    from app.services.symbolic_checker import SymbolicChecker
    from app.services.provenance_engine import ProvenanceEngine

    task_uuid = uuid.UUID(task_id)
    db = _get_sync_db()

    try:
        # ── Step 1: Update task status to "processing" ──
        task_row = db.query(Task).filter(Task.id == task_uuid).first()
        if not task_row:
            logger.error(f"Task {task_id} not found in DB")
            return {"error": "task_not_found"}

        task_row.status = "processing"
        task_row.progress_percent = 10
        db.commit()

        # ── Step 2: Download PDF from MinIO ──
        logger.info(f"Downloading PDF from MinIO: {object_key}")
        s3 = _get_minio_client()
        response = s3.get_object(Bucket=settings.minio_bucket, Key=object_key)
        pdf_bytes = response["Body"].read()

        # ── Step 3: Extract text from PDF bytes via pdfplumber ──
        import pdfplumber
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        task_row.progress_percent = 25
        db.commit()
        logger.info(f"Extracted {len(text)} characters from PDF")

        # ── Step 4: Semantic chunking ──
        chunker = SemanticChunker()
        chunks = chunker.chunk(text)
        logger.info(f"Created {len(chunks)} semantic chunks")

        task_row.progress_percent = 40
        db.commit()

        # ── Step 5: Generate embeddings and store chunks ──
        embedding_service = EmbeddingService()
        stored_count = embedding_service.embed_and_store(task_uuid, chunks, db)

        task_row.progress_percent = 60
        db.commit()

        # ── Step 6: Symbolic rule checks ──
        checker = SymbolicChecker()
        symbolic_result = checker.check(text)

        # ── Step 7: Provenance logging ──
        provenance = ProvenanceEngine(task_uuid, db)
        provenance.log_symbolic_checks(symbolic_result)
        db.commit()

        # ── Step 8: Dispatch async tasks in a chord ──
        # Use first available chunk text as context for agents
        context_text = chunks[0].text[:2000] if chunks else text[:2000]
        
        async_tasks = []

        for agent in AGENT_GROUPS:
            async_tasks.append(
                run_agent_task.s(
                    task_id=task_id,
                    agent_name=agent["name"],
                    agent_label=agent["label"],
                    prompt=agent["prompt_template"].format(text=context_text),
                    schema=agent["schema"],
                ).set(queue="llm_bound")
            )

        # ── Step 9: Dispatch Phase 3 External Enrichment & Matching ──
        async_tasks.append(enrich_references_task.s(task_id=task_id, text=text).set(queue="io_bound"))
        async_tasks.append(match_journals_task.s(task_id=task_id).set(queue="io_bound"))
        
        # ── Mark task as agents_running before chord ──
        task_row.status = "agents_running"
        task_row.progress_percent = 80
        task_row.dashboard_payload = {
            "chunks": stored_count,
            "symbolic_check": symbolic_result.to_dict(),
        }
        db.commit()

        # Execute chord: wait for all async_tasks to finish, then call finalize_analysis_task
        chord(async_tasks)(finalize_analysis_task.s(task_id=task_id).set(queue="io_bound"))

        logger.info(f"Pipeline chord dispatched for task {task_id}")
        return {
            "task_id": task_id,
            "chunks_stored": stored_count,
            "symbolic_issues": symbolic_result.issues,
            "status": "chord_dispatched"
        }

    except Exception as exc:
        logger.error(f"extract_pdf_task failed for task {task_id}: {exc}", exc_info=True)
        try:
            task_row = db.query(Task).filter(Task.id == task_uuid).first()
            if task_row:
                task_row.status = "failed"
                task_row.dashboard_payload = {"error": str(exc)}
                db.commit()
        except Exception:
            pass
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))

    finally:
        db.close()


@celery_app.task(bind=True, name="app.worker.tasks.run_agent_task", max_retries=2)
def run_agent_task(
    self,
    task_id: str,
    agent_name: str,
    agent_label: str,
    prompt: str,
    schema: dict,
) -> dict:
    """
    llm_bound worker: Execute a single LLM agent group with cascade fallback.

    Steps:
        1. Send structured JSON prompt to OllamaAgent (Ollama → NVIDIA NIM → Gemini → OpenAI)
        2. Validate and parse JSON response
        3. Merge agent result into task dashboard_payload
        4. Log to provenance_log

    Args:
        task_id: UUID string for the analysis task.
        agent_name: Short machine-readable agent name.
        agent_label: Human-readable label (e.g., "Group A - Document Intelligence").
        prompt: Full prompt text for the agent.
        schema: Expected JSON response schema.

    Returns:
        Parsed agent result dict.
    """
    from app.models.models import Task
    from app.services.ollama_agent import OllamaAgent
    from app.services.provenance_engine import ProvenanceEngine

    task_uuid = uuid.UUID(task_id)
    db = _get_sync_db()

    try:
        agent = OllamaAgent()
        logger.info(f"Running agent: {agent_label} for task {task_id}")

        result = agent.run(agent_name=agent_label, prompt=prompt, schema=schema)

        # Determine which provider succeeded (stored in result if degraded)
        provider = "Ollama" if result.get("status") != "degraded" else "degraded"

        # Persist provenance entry
        provenance = ProvenanceEngine(task_uuid, db)
        provenance.log_agent_result(agent_label, result, provider_used=provider)

        # Merge result into task dashboard_payload
        task_row = db.query(Task).filter(Task.id == task_uuid).first()
        if task_row:
            payload = task_row.dashboard_payload or {}
            if "agents" not in payload:
                payload["agents"] = {}
            payload["agents"][agent_name] = result
            task_row.dashboard_payload = payload
            db.commit()

        logger.info(f"Agent {agent_label} completed successfully (provider={provider})")
        return result

    except Exception as exc:
        logger.error(f"run_agent_task failed for {task_id}, agent {agent_name}: {exc}")
        return {"error": str(exc)}


@celery_app.task(bind=True, max_retries=3)
def enrich_references_task(self, task_id: str, text: str) -> dict:
    """
    Extracts DOIs from the text, verifies them with Crossref,
    and fetches citation stats from OpenAlex.
    """
    logger.info(f"Starting enrich_references_task for {task_id}")
    
    # Extract DOIs using a basic regex
    doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"
    found_dois = list(set(re.findall(doi_pattern, text, re.IGNORECASE)))
    
    # Limit to first 10 to avoid API rate limits during processing
    dois_to_process = found_dois[:10]
    
    async def process_dois(dois):
        import redis.asyncio as aioredis
        import json
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        
        crossref = CrossrefClient()
        openalex = OpenAlexClient()
        results = []
        for doi in dois:
            cache_key = f"doi_cache:{doi}"
            cached = await redis_client.get(cache_key)
            if cached:
                try:
                    results.append(json.loads(cached))
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse Redis cache for {doi}: {e}")
            
            # 1. Verify with Crossref
            cr_res = await crossref.verify_doi(doi)
            if not cr_res:
                continue
                
            # 2. Get stats from OpenAlex
            oa_res = await openalex.get_work_by_doi(doi)
            
            result = {
                "crossref": cr_res,
                "openalex": oa_res,
            }
            results.append(result)
            
            # Cache for 30 days
            try:
                await redis_client.setex(cache_key, 86400 * 30, json.dumps(result))
            except Exception as e:
                logger.warning(f"Failed to write to Redis cache for {doi}: {e}")
                
            # Be polite to rate limits
            await asyncio.sleep(0.5)
        return results

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    results = loop.run_until_complete(process_dois(dois_to_process))
    
    # Save to ProvenanceLog
    sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        from app.models.models import ProvenanceLog
        log_entry = ProvenanceLog(
            task_id=uuid.UUID(task_id),
            metric_name="reference_enrichment",
            metric_value={"enriched_references": results, "total_found": len(found_dois)},
            formula_used="Regex DOI extraction + Crossref + OpenAlex",
            data_sources=["crossref", "openalex"],
            confidence_level="high",
        )
        db.add(log_entry)
        db.commit()
    finally:
        db.close()
        
    return {"enriched_count": len(results)}


@celery_app.task(bind=True, max_retries=3)
def match_journals_task(self, task_id: str) -> dict:
    """
    Matches the manuscript's embeddings against known journals in the DB.
    """
    logger.info(f"Starting match_journals_task for {task_id}")
    
    sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        matcher = JournalMatcher(db)
        matches = matcher.find_matching_journals(uuid.UUID(task_id), top_k=5)
        
        # Save to ProvenanceLog
        from app.models.models import ProvenanceLog
        log_entry = ProvenanceLog(
            task_id=uuid.UUID(task_id),
            metric_name="journal_matches",
            metric_value={"matches": matches},
            formula_used="pgvector cosine distance (1 - <=>)",
            data_sources=["journals", "doaj"],
            confidence_level="high",
        )
        db.add(log_entry)
        db.commit()
        return {"matches_found": len(matches)}
    finally:
        db.close()


@celery_app.task(bind=True, name="app.worker.tasks.finalize_analysis_task")
def finalize_analysis_task(self, results, task_id: str):
    """
    Called automatically as a Celery chord callback when all LLM agents and 
    Phase 3 tasks (enrichment, matching) finish executing.
    """
    from app.models.models import Task, ProvenanceLog
    task_uuid = uuid.UUID(task_id)
    db = _get_sync_db()
    
    try:
        task_row = db.query(Task).filter(Task.id == task_uuid).first()
        if task_row:
            matches_log = db.query(ProvenanceLog).filter(
                ProvenanceLog.task_id == task_uuid,
                ProvenanceLog.metric_name == "journal_matches"
            ).first()
            
            enrich_log = db.query(ProvenanceLog).filter(
                ProvenanceLog.task_id == task_uuid,
                ProvenanceLog.metric_name == "reference_enrichment"
            ).first()

            payload = dict(task_row.dashboard_payload) if task_row.dashboard_payload else {}
            
            if matches_log and matches_log.metric_value:
                payload["journal_matches"] = matches_log.metric_value.get("matches", [])
                
            if enrich_log and enrich_log.metric_value:
                payload["reference_enrichment"] = enrich_log.metric_value.get("enriched_references", [])
                
            task_row.dashboard_payload = payload
            task_row.status = "completed"
            task_row.progress_percent = 100
            db.commit()
            logger.info(f"Pipeline finalized and marked as completed for task {task_id}")
    except Exception as exc:
        logger.error(f"Error finalizing task {task_id}: {exc}")
    finally:
        db.close()
    
    return {"status": "finalized"}
