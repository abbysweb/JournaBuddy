# JournaBuddy – Comprehensive System Design & Detailed Implementation Plan

**Author:** Abdullah Al Mamun (BSc, MSc - Software Engineering)  
**Affiliations:** TU Wien (Vienna, Austria) & Daffodil International University  
**Contact:** mamun.swe.de@gmail.com | **GitHub:** [@abbysweb](https://github.com/abbysweb) | **ORCID:** [0009-0006-7473-0024](https://orcid.org/0009-0006-7473-0024)  
**Project:** JournaBuddy – Research Paper Intelligence Platform  
**Status:** Transitioning from Module 1 MVP to Production-Grade Hybrid Architecture  
**Goal:** Build a horizontally scalable, open-source platform combining symbolic rules, statistical NLP, and semantic LLM agents with verifiable provenance and zero vendor lock-in.

---

## 1. Vision & Core Philosophy

JournaBuddy assists authors in preparing, optimizing, and evaluating scientific manuscripts before submission by combining three complementary intelligence layers:

1. **Symbolic / Rule-Based Layer (Module 1):** Precise, deterministic checks (structure, acronym definitions, reference formatting, grammar).
2. **Statistical NLP Layer (Module 4):** Continuous, benchmarkable metrics (Flesch-Kincaid readability, passive voice density, lexical diversity, jargon extraction).
3. **Semantic / Embedding Layer (Modules 2 & 4):** Meaning extraction, vector similarity, knowledge graphs, and local LLM agent evaluation.

### Core Questions Addressed by the System:
* **Module 1 (Manuscript Readiness Checker):** *Is my paper structurally and grammatically ready for submission?*
* **Module 2 (Journal Discovery & Matching):** *Which peer-reviewed journals fit the scope and domain of my manuscript?*
* **Module 3 (Journal Trust Scorer):** *Are the target journals reputable, indexed, and trustworthy?*
* **Module 4 (BI Dashboard & Field Benchmarking):** *How does my manuscript quantitatively compare against top published papers in its specific field?*

---

## 2. Master Technology Stack

| Layer | Technology | License | System Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React 19 + TypeScript + Vite | MIT | High-performance, reactive UI |
| **Styling & UI** | TailwindCSS 4 + Glassmorphism | MIT | Modern, premium design tokens |
| **Data Visualization** | Apache ECharts & vis-network | Apache / MIT | Radar charts, gauge metrics, citation graphs |
| **State Management** | Zustand & TanStack Query | MIT | Global UI state & server-side query caching |
| **API Server** | FastAPI (Python 3.10+) | MIT | High-throughput asynchronous backend |
| **ORM & Migrations** | SQLAlchemy 2 + Alembic | MIT | Database modeling & migration management |
| **Distributed Queue** | Celery 5 | BSD | Async worker execution & parallel agent chords |
| **Message Broker & Cache** | Redis 7 | BSD | Task queuing, prompt caching, SSE Pub/Sub |
| **Database & Vectors** | PostgreSQL 16 + `pgvector` | PostgreSQL / MIT | Unified relational data & 384-dim vector search |
| **Object Storage** | MinIO | AGPLv3 | Self-hosted S3-compatible PDF binary store |
| **Local LLM Serving** | Ollama (Llama 3.1:8b / Mistral) | MIT | Offline, zero-cost AI agent inference |
| **Text Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Apache 2.0 | Fast semantic vectorization (384 dimensions) |
| **PDF Extraction** | `pdfplumber` + `PyMuPDF` | MIT | Layout-aware text and metadata extraction |
| **Reverse Proxy** | Nginx | BSD | SSL termination, static asset serving, rate limits |
| **Observability** | Prometheus + Grafana + Jaeger | Apache 2.0 | System metrics, distributed tracing, error logs |

---

## 3. High-Level Architecture & End-to-End Data Flow

```
+-----------------------------------------------------------------------------+
|                            CLIENT LAYER (Browser)                           |
|       React 19 + TypeScript App  │  TailwindCSS  │  ECharts Dashboard       |
+----------------------------------┼------------------------------------------+
                                   │ (HTTP / SSE / REST)
                                   ▼
+-----------------------------------------------------------------------------+
|                         GATEWAY LAYER (Nginx Proxy)                         |
|     • SSL Termination    • /api/* Proxy    • Static Files    • Rate Limits   |
+----------------------------------┼------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------------+
|                         API LAYER (FastAPI Async)                           |
|  • Upload Endpoint (/api/upload)         • SSE Streaming (/api/stream/{id}) |
|  • JWT Auth & Security Middlewares       • Provenance Endpoint              |
+----------------─┬────────────────┼─────────────────┬------------------------+
                  │                │                 │
                  ▼                ▼                 ▼
          +---------------+  +-----------+    +-------------+
          |  PostgreSQL   |  |   Redis   |    |    MinIO    |
          |  (+pgvector)  |  | Broker &  |    | PDF Binary  |
          | Relational DB |  | Pub/Sub   |    | Object Store|
          +---------------+  +-----+-----+    +-------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------------+
|                         WORKER LAYER (Celery Engine)                        |
|  • Parallel Agent Group Execution  • PDF Extraction Pipeline               |
|  • External Enrichment (Crossref, OpenAlex, DOAJ)                          |
+----------------------------------┼------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------------+
|                      INFERENCE LAYER (Local Ollama)                         |
|    • Ollama-1 (Llama 3.1)    • Ollama-2 (Mistral)    • Embeddings Engine    |
+-----------------------------------------------------------------------------+
```

### Detailed 8-Step Data Pipeline Execution:

1. **Upload & Ingestion:** Author uploads PDF/DOCX via FastAPI (`POST /api/upload`). File is assigned a UUID `task_id` and saved in MinIO.
2. **Symbolic Analysis:** Worker extracts raw layout and text (`pdfplumber`). Runs deterministic rule checkers for section headers, acronym resolution, reference-to-citation linking, and grammar.
3. **Statistical NLP:** Evaluates readability formulas (Flesch-Kincaid), passive voice percentages, lexical diversity, and academic jargon density via `textstat` and `spaCy`.
4. **Semantic Vectorization:** Chunks text into logical paragraphs, computes 384-dimensional embeddings via `sentence-transformers`, and stores them in PostgreSQL using `pgvector`.
5. **Parallel Agent Orchestration:** Celery executes 6 concurrent LLM agent groups using local Ollama models:
   * **Group A (Document Intelligence):** Title, authors, core keywords, domain classification.
   * **Group B (Language & Compliance):** Tone, formality, academic voice adherence.
   * **Group C (Originality & Risk):** Potential similarity patterns, novelty summary.
   * **Group D (Research Rigor):** Methodology completeness, dataset declarations, statistical validity.
   * **Group E (Journal Scope Fit):** Semantic relevance to target field journal scopes.
   * **Group F (Peer Review Simulation):** Generates feedback from 3 distinct reviewer personas (Strict Methodologist, Domain Expert, General Reader).
6. **Async External Enrichment:** Cross-references citations against OpenAlex for citation counts, Crossref for DOI validation, and DOAJ for journal trust indexing.
7. **Field Benchmarking:** Compares manuscript metrics against precomputed field averages.
8. **Convergence & SSE Streaming:** Results are combined into a final payload, written to the `provenance_log` database table, and streamed directly to the user's browser over SSE.

---

## 4. Database Schema Specification (PostgreSQL + pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Task Orchestration Table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress_percent INTEGER DEFAULT 0,
    dashboard_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Semantic Document Chunks (pgvector)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section_name VARCHAR(100),
    text_content TEXT NOT NULL,
    embedding VECTOR(384)
);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Provenance & Verifiability Log
CREATE TABLE provenance_log (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    formula_used TEXT,
    data_sources TEXT[],
    confidence_level VARCHAR(20),
    raw_data_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Journal Master Table
CREATE TABLE journals (
    id SERIAL PRIMARY KEY,
    issn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    publisher VARCHAR(255),
    is_doaj_indexed BOOLEAN DEFAULT FALSE,
    trust_score NUMERIC(4, 2),
    scope_embedding VECTOR(384)
);
```

---

## 5. Granular Phase-by-Phase Implementation Roadmap

### Phase 1: Foundation & Data Infrastructure (Completed / In Verification)
* [x] Scaffold Docker Compose environment (`api`, `postgres`, `redis`, `minio`, `nginx`, `ollama-1`, `prometheus`, `grafana`).
* [x] Setup `.env` configuration template with Postgres, Redis, and MinIO credentials.
* [x] Build FastAPI base server structure with `/health` and `/api/upload` endpoints.
* [x] Build initial PDF extraction utility using `pdfplumber`.
* [x] Scaffold Vite + React 19 + TypeScript frontend application.
* [x] Organize project directory into standardized `/docs`, `/scripts`, `/data`, and `/archive` folders.
* [x] Create project test cases in `/test_cases/phase_1_verification.md`.

### Phase 2: Intelligence Pipeline & Celery Agent Orchestration (Weeks 3-4)
* [x] Setup Celery task queue with `io_bound` and `llm_bound` worker pools.
* [x] Integrate Ollama (`Llama 3.1:8b`) with structured JSON schema outputs and 4-provider cascade fallback (Ollama → NVIDIA NIM → Gemini → OpenAI).
* [x] Implement semantic chunking strategy and `sentence-transformers` vectorization (all-MiniLM-L6-v2, 384 dimensions, stored in `pgvector`).
* [x] Implement the `ProvenanceEngine` service to populate `provenance_log` with formula, data sources, confidence level, and raw data snapshots.
* [x] Build rule-based symbolic checks for acronyms, paper section completeness, passive voice density, and Flesch-Kincaid readability.
* [x] Create Phase 2 test cases in `/test_cases/phase_2_verification.md`.

### Phase 3: External Enrichment & Journal Matching (Weeks 5-6)
* [ ] Build async OpenAlex API client to fetch author profiles and paper citation statistics.
* [ ] Integrate Crossref API for reference DOI verification.
* [ ] Integrate DOAJ API for journal legitimacy scoring (Module 3).
* [ ] Implement `pgvector` cosine similarity search to match manuscript embeddings against journal scopes (Module 2).
* [ ] Create Phase 3 test cases in `/test_cases/phase_3_verification.md`.

### Phase 4: Real-Time UI & Interactive Dashboard (Week 7)
* [ ] Build FastAPI Server-Sent Events (SSE) endpoint `/api/stream/{task_id}` for live progress streaming.
* [ ] Implement modern Glassmorphism UI components in React.
* [ ] Build interactive Apache ECharts visualizations (Quality Radar Chart, Readiness Gauge, Jargon Heatmap).
* [ ] Integrate `vis-network` for interactive citation graph rendering.
* [ ] Implement expandable provenance tooltips for total score verifiability.
* [ ] Create Phase 4 test cases in `/test_cases/phase_4_verification.md`.

### Phase 5: Production Hardening & Observability (Week 8)
* [ ] Implement content-addressable Redis caching for duplicate paper uploads.
* [ ] Setup Prometheus metrics scraping for token usage, latency, and memory consumption.
* [ ] Build Grafana monitoring dashboards.
* [ ] Implement JWT Authentication and rate-limiting using `slowapi`.
* [ ] Create GitHub Actions for automated testing and nightly benchmarking updates.
* [ ] Create Phase 5 test cases in `/test_cases/phase_5_verification.md`.

---

## 6. Error Handling & System Resilience Strategy

To ensure zero downtime and prevent cascading system failures during document evaluation, JournaBuddy implements multi-tier error resilience:

### 6.1 Worker & Parallel Agent Graceful Fallbacks
* **Agent Isolation:** Each of the 6 parallel LLM agent groups runs inside an isolated `try-except` execution block. If one agent fails or times out, the remaining 5 agents complete successfully.
* **Partial Output Degraded Mode:** If an agent encounters a fatal error, it returns a partial result payload (`{"status": "degraded", "score": null, "reason": "Model VRAM timeout"}`) to ensure the author still gets the rest of their analysis.
* **Celery Retries with Backoff:** Network-bound errors use exponential backoff (`max_retries=3`, `countdown=5`) via Celery and `tenacity`.

### 6.2 Multi-Tier LLM Provider Cascade
If the local Ollama instance is overloaded or unreachable, the system automatically cascades through backup LLM providers:
1. **Primary:** Local Ollama (`Llama 3.1:8b`).
2. **Fallback 1:** NVIDIA NIM API.
3. **Fallback 2:** Gemini API.
4. **Fallback 3:** OpenAI API.

### 6.3 API Layer Exception Handling & Cleanup
* **Structured Error Schemas:** FastAPI returns uniform, machine-readable JSON error payloads (`{"status": "error", "error_code": "PDF_CORRUPTED", "message": "..."}`).
* **Automatic File Cleanup:** Storage utilities execute `finally` blocks to remove temporary processing binaries from disk if parsing is aborted.

### 6.4 Circuit Breakers for External Academic APIs
* **Strict Timeouts:** All async calls to OpenAlex, Crossref, and DOAJ enforce a 5-second timeout.
* **Cache Fallback:** If an external API is offline, JournaBuddy serves cached historical paper metrics from Redis.

---

## 7. Testing & Quality Assurance Strategy

To ensure data integrity, vector search accuracy, and zero runtime crashes, testing is broken down into 5 distinct layers:

### 7.1 Unit & Formula Logic Testing (`pytest`)
* **Scope:** `pdfplumber` layout parser accuracy, `textstat` Flesch-Kincaid readability formula, symbolic acronym resolution, and Pydantic prompt schema validation.
* **Execution:** Run automated `pytest` test suites in `backend/`.

### 7.2 API & Integration Testing (`httpx` / FastAPI `TestClient`)
* **Scope:** `GET /health` sanity check, `POST /api/upload` PDF storage in MinIO, non-PDF input rejection (`400 Bad Request`), and payload size limits (`50MB`).

### 7.3 Vector & Database Testing (PostgreSQL + `pgvector`)
* **Scope:** Cosine distance calculation accuracy (`1 - (embedding <=> scope)`), `provenance_log` audit entries, database index performance, and migration integrity.

### 7.4 Worker & LLM Agent Testing (Celery + Ollama)
* **Scope:** Parallel task routing (`io_bound` vs `llm_bound`), local LLM JSON output validation, fallback cascading (Ollama -> NVIDIA NIM -> Gemini -> OpenAI), and VRAM memory leak prevention.

### 7.5 End-to-End UI & Real-Time Streaming Testing (React + Vite)
* **Scope:** Server-Sent Events (SSE) `/api/stream/{task_id}` connectivity, Apache ECharts responsiveness, side-by-side PDF rendering, and glassmorphic UI layout.

---

## 8. Advanced Production Features & Enhancements

To establish JournaBuddy as a state-of-the-art research intelligence platform, the system incorporates 5 advanced features:

### 8.1 3-Persona AI Peer Reviewer Simulation
* **Strict Methodologist:** Audits sample sizes, experimental controls, baseline comparisons, and statistical validity.
* **Domain Specialist:** Evaluates paper novelty, literature gaps, and citation completeness.
* **Copy & Academic Style Editor:** Audits tone, jargon clarity, passive voice density, and figure/table references.

### 8.2 Interactive Bounding Box PDF Annotations
* Clicking on any extracted warning or suggestion in the dashboard automatically highlights the exact paragraph and section on the embedded PDF canvas using bounding box coordinates.

### 8.3 BibTeX Auto-Fixer & 2D/3D Citation Graph
* **BibTeX Auto-Fixer:** Queries Crossref and OpenAlex to resolve broken DOIs or incomplete entries, enabling a 1-click download of a corrected `.bib` file.
* **Citation Graph Explorer:** Visualizes the manuscript as a central node connected to cited works and field-defining papers via `vis-network`.

### 8.4 Journal Scope Fit & Acceptance Likelihood Predictor
* Computes vector cosine distance between abstract embeddings and historical published paper abstracts across top journals to estimate domain compatibility percentages.

### 8.5 Exportable Manuscript Proof Report (PDF)
* Generates a downloadable PDF evaluation certificate (via LaTeX/`reportlab`) summarizing readability metrics, trust scores, and reviewer reports for co-authors and advisors.

---

## 9. Verification & Automated Commit Protocols

Following the system execution rules:
1. **Verification First:** Each phase must be verified using the specific test cases in `test_cases/phase_X_verification.md`.
2. **Proof Artifacts:** A walkthrough document (`walkthrough.md`) and proof of test completion will be generated upon phase completion.
3. **Automated Commit & Push:** After phase completion and verification, changes will be automatically staged, committed with a descriptive message, and pushed to GitHub.
