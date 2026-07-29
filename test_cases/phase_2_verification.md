# Phase 2 Test Cases — Intelligence Pipeline & Celery Agent Orchestration

## Overview
These test cases verify the complete Phase 2 intelligence pipeline: Celery task routing,
semantic chunking, pgvector embedding storage, Ollama LLM agent invocation, ProvenanceEngine
audit trail, and symbolic rule checking.

---

## Test Case 1: Celery Worker Pool Routing

- **Action**: After `podman compose up -d`, inspect worker logs:
  ```bash
  podman logs journabuddy_worker-io_1 --tail 20
  podman logs journabuddy_worker-llm_1 --tail 20
  ```
- **Expected Result**:
  - `worker-io` registers as listening on queue: `io_bound`
  - `worker-llm` registers as listening on queue: `llm_bound`
  - No `broker_connection_retry` deprecation warning in logs

---

## Test Case 2: PDF Upload → Task Queued

- **Action**: Upload a sample PDF via the API:
  ```bash
  curl -X POST -F "file=@data/sample.pdf" http://localhost:8000/api/upload
  ```
- **Expected Result**:
  ```json
  {
    "task_id": "<uuid>",
    "filename": "sample.pdf",
    "status": "queued",
    "message": "PDF uploaded successfully. Analysis pipeline is running."
  }
  ```
  - File appears in MinIO dashboard (`http://localhost:9001`) under bucket `journabuddy-uploads`
  - A row exists in the `tasks` table with `status = 'queued'`

---

## Test Case 3: Task Status Polling & Pipeline Progression

- **Action**: Poll task status:
  ```bash
  curl http://localhost:8000/api/task/<task_id>
  ```
- **Expected Result**: Status progresses through:
  `queued` → `processing` → `agents_running` → (agent results populated)
- `progress_percent` increases from 0 → 10 → 25 → 40 → 60 → 75 → 80

---

## Test Case 4: Semantic Chunking & pgvector Storage

- **Action**: After upload, connect to Postgres and query:
  ```sql
  SELECT chunk_index, section_name, length(text_content), 
         jsonb_array_length(embedding_json)
  FROM document_chunks 
  WHERE task_id = '<task_id>'
  ORDER BY chunk_index;
  ```
- **Expected Result**:
  - Multiple rows with `section_name` matching academic sections (Abstract, Introduction, etc.)
  - `jsonb_array_length(embedding_json) = 384` confirming correct vector dimensions

---

## Test Case 5: Symbolic Rule Checker Results

- **Action**: Query `provenance_log` for symbolic check metrics:
  ```sql
  SELECT metric_name, metric_value, formula_used, confidence_level
  FROM provenance_log
  WHERE task_id = '<task_id>'
  AND metric_name IN ('flesch_reading_ease', 'passive_voice_density',
                       'acronym_check', 'section_completeness');
  ```
- **Expected Result**:
  - 4 rows returned (one per symbolic metric)
  - Each row contains `formula_used` with the mathematical formula used
  - `confidence_level = 'high'` for deterministic metrics
  - `metric_value` is a valid JSONB object

---

## Test Case 6: Ollama LLM Agent JSON Output

- **Action**: After pipeline runs, query agent results:
  ```sql
  SELECT metric_name, metric_value, confidence_level
  FROM provenance_log
  WHERE task_id = '<task_id>'
  AND metric_name LIKE 'agent_%';
  ```
  Or poll task status for `dashboard_payload.agents`:
  ```bash
  curl http://localhost:8000/api/task/<task_id>
  ```
- **Expected Result**:
  - `agent_document_intelligence` row with `title`, `keywords`, `domain` fields
  - `agent_language_compliance` row with tone/formality scores
  - `agent_research_rigor` row with methodology and statistical validity scores
  - If Ollama is still pulling the model: `status = "degraded"` with fallback to NVIDIA NIM

---

## Test Case 7: ProvenanceEngine Audit Trail

- **Action**:
  ```sql
  SELECT COUNT(*), array_agg(metric_name)
  FROM provenance_log
  WHERE task_id = '<task_id>';
  ```
- **Expected Result**:
  - At least 7 provenance entries per task (4 symbolic + 3 agent groups)
  - Each entry has non-null `data_sources` and `created_at` timestamp

---

## Test Case 8: LLM Cascade Fallback (NVIDIA NIM)

- **Action**: Stop the Ollama container and upload a new PDF:
  ```bash
  podman stop journabuddy_ollama-1_1
  curl -X POST -F "file=@data/sample.pdf" http://localhost:8000/api/upload
  ```
- **Expected Result**:
  - Worker log shows: `Provider Ollama failed: ...`
  - Worker log shows: `Trying provider: NVIDIA NIM`
  - NVIDIA NIM returns valid JSON agent response
  - Provenance entry records `data_sources: ["NVIDIA NIM"]`

---

## Test Case 9: Invalid File Type Rejection

- **Action**:
  ```bash
  curl -X POST -F "file=@README.md" http://localhost:8000/api/upload
  ```
- **Expected Result**:
  ```json
  {"detail": {"status": "error", "error_code": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted."}}
  ```
  HTTP Status: `400 Bad Request`

---

## Test Case 10: Task Not Found

- **Action**:
  ```bash
  curl http://localhost:8000/api/task/00000000-0000-0000-0000-000000000000
  ```
- **Expected Result**:
  ```json
  {"detail": {"status": "error", "error_code": "TASK_NOT_FOUND", "message": "..."}}
  ```
  HTTP Status: `404 Not Found`
