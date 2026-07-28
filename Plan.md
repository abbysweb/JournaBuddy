# JournaBuddy – Complete Implementation Plan

**Author:** Abdullah Al Mamun (ORCID: 0009-0006-7473-0024)  
**Project:** JournaBuddy – Research Paper Intelligence Platform  
**Status:** Module 1 MVP built.  
**Goal:** Build a full hybrid system with modern UI, data security, error handling, and mathematical provenance.

---

## 1. Vision & Core Philosophy

JournaBuddy helps authors prepare manuscripts by combining three analysis layers:

- **Symbolic / rule‑based** – precise, explainable checks (Module 1).
- **Statistical NLP** – continuous, benchmarkable metrics (Module 4).
- **Semantic / embedding + knowledge graph** – meaning and relationships (Modules 2, 4).

The system answers four questions:

| Question | Module |
|----------|--------|
| *Is my paper ready to submit?* | Module 1: Manuscript Readiness Checker |
| *Which journals fit my paper?* | Module 2: Journal Discovery & Matching |
| *Are those journals trustworthy?* | Module 3: Journal Trust Scorer |
| *How does my paper compare to its field?* | Module 4: BI Dashboard & Benchmarking |

**Core principles:** radical transparency, hybrid intelligence, user‑centric design, security & privacy by design, zero‑cost infrastructure.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (HTML/JS/CSS)                       │
│                     Glass‑morphism UI, Chart.js, vis‑network         │
│                     Tooltips & expandable provenance panels          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ REST (FastAPI)
┌─────────────────────────────────▼───────────────────────────────────┐
│                         FastAPI Backend                              │
│  • /api/upload               • /api/status/{task_id}                 │
│  • /api/health               • /api/journals/search (Module 2)      │
│  • /api/journals/trust (M3)  • /api/benchmark (M4)                  │
│  • /api/insights/{task_id}   • /api/provenance/{metric_id}          │
└─────────────┬───────────────────┬───────────────────┬───────────────┘
              │                   │                   │
    ┌─────────▼────────┐  ┌──────▼──────┐  ┌─────────▼────────┐
    │ Symbolic Layer    │  │ Statistical │  │ Semantic Layer   │
    │ (Module 1)        │  │ NLP Layer   │  │ (Embeddings)     │
    │ • Rule engine     │  │ • textstat  │  │ • sentence‑      │
    │ • LanguageTool    │  │ • spaCy     │  │   transformers   │
    │ • PDF/DOCX parser │  │ • wordfreq  │  │ • KeyBERT        │
    └───────────────────┘  └─────────────┘  └─────────┬─────────┘
                                                      │
                                            ┌─────────▼────────┐
                                            │ External Enrichment │
                                            │ (Async)           │
                                            │ • Crossref        │
                                            │ • OpenAlex        │
                                            │ • DOAJ / COPE     │
                                            └─────────┬─────────┘
                                                      │
┌─────────────────────────────────────────────────────▼─────────────────────┐
│                          Postgres + pgvector (Supabase)                     │
│  • tasks          • journals        • journal_metrics    • trust_flags     │
│  • refs_cache     • insights       • field_benchmarks                       │
│  • provenance_log – stores every calculation result with metadata           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Deployment:**
- Backend: FastAPI on **Render** or **Fly.io** free tier.
- Database: **Supabase** free tier (Postgres + pgvector).
- Worker: **RQ** with Redis (Redis Cloud free or local). Fallback to threading.
- Scheduled jobs: **GitHub Actions** cron (nightly).
- Frontend: served by FastAPI or hosted on **Vercel/Netlify**.

---

## 3. Hybrid Data Flow (End‑to‑End)

1. Upload PDF/DOCX → extract text, references, metadata.
2. Run **symbolic checks** (Module 1): structure, acronyms, citation‑reference, grammar.
3. Run **statistical NLP** (Module 4): readability, passive voice, lexical diversity, jargon.
4. Async enrichment: resolve references via Crossref, fetch citation data from OpenAlex, build citation graph.
5. Embed abstract, extract keywords (KeyBERT), compute topic similarity.
6. Compare against field benchmarks (precomputed nightly).
7. Aggregate all results into one JSON payload with provenance IDs.
8. Frontend renders dashboard with provenance tooltips.

---

## 4. Database Schema (Postgres + pgvector)

```sql
-- Task tracking
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    status TEXT,
    current_agent TEXT,
    completed_agents JSONB,
    result JSONB,
    error TEXT,
    timestamp TIMESTAMP
);

-- Journal registry
CREATE TABLE journals (
    id SERIAL PRIMARY KEY,
    issn TEXT UNIQUE,
    eissn TEXT,
    title TEXT NOT NULL,
    publisher TEXT,
    openalex_id TEXT,
    is_oa BOOLEAN DEFAULT FALSE,
    scope_description TEXT,
    scope_embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Journal metrics
CREATE TABLE journal_metrics (
    journal_id INT REFERENCES journals(id),
    year INT,
    works_count INT,
    cited_by_count INT,
    h_index INT,
    two_yr_mean_citedness FLOAT,
    PRIMARY KEY (journal_id, year)
);

-- Trust signals
CREATE TABLE journal_trust_flags (
    journal_id INT REFERENCES journals(id) PRIMARY KEY,
    in_doaj BOOLEAN DEFAULT FALSE,
    doaj_seal BOOLEAN DEFAULT FALSE,
    cope_member BOOLEAN DEFAULT FALSE,
    oaspa_member BOOLEAN DEFAULT FALSE,
    retraction_count INT DEFAULT 0,
    last_checked TIMESTAMP DEFAULT now()
);

-- Resolved references cache
CREATE TABLE resolved_references (
    id SERIAL PRIMARY KEY,
    raw_citation_text TEXT,
    doi TEXT UNIQUE,
    title TEXT,
    year INT,
    venue_type TEXT,
    openalex_id TEXT,
    cited_by_count INT,
    concepts JSONB,
    resolved_at TIMESTAMP DEFAULT now()
);

-- Per-manuscript insights
CREATE TABLE manuscript_insights (
    manuscript_check_id INT PRIMARY KEY,
    readability JSONB,
    citation_analytics JSONB,
    topic_analytics JSONB,
    benchmark_comparison JSONB,
    provenance_ids JSONB,
    computed_at TIMESTAMP DEFAULT now()
);

-- Field benchmarks
CREATE TABLE field_benchmarks (
    openalex_concept_id TEXT PRIMARY KEY,
    concept_name TEXT,
    avg_word_count FLOAT,
    avg_reference_count FLOAT,
    avg_reference_recency_years FLOAT,
    sample_size INT,
    computed_at TIMESTAMP DEFAULT now()
);

-- Provenance log
CREATE TABLE provenance_log (
    id SERIAL PRIMARY KEY,
    task_id TEXT,
    metric_name TEXT,
    metric_value JSONB,
    formula TEXT,
    data_sources TEXT[],
    confidence_level TEXT,
    timestamp TIMESTAMP,
    raw_data_snapshot JSONB,
    explanation TEXT
);
```

---

## 5. Technology Stack (100% Free / Open‑Source)

| Layer | Choice |
|-------|--------|
| Backend | FastAPI |
| Database | Supabase (Postgres + pgvector) |
| LLM | NVIDIA NIM (primary) → Gemini → OpenAI → Ollama |
| Embeddings | sentence‑transformers (all‑MiniLM‑L6‑v2) |
| Grammar | LanguageTool (self‑hosted) |
| PDF/DOCX | PyMuPDF, python‑docx |
| Frontend | Plain HTML/JS (or React later) |
| Hosting | Render/Fly.io (backend), Vercel/Netlify (frontend) |
| Scheduled jobs | GitHub Actions |
| Charts | Chart.js, vis‑network |
| Security | slowapi (rate limiting), python‑jose (JWT), tenacity (retries) |

---

## 6. UI Design System – Modern Glassmorphism

**Theme:** Sage Green & Glassmorphism.

**Colors:**
- Primary: `#2b4c3f`
- Secondary: `#0c1a14`
- Accent: `#38bdf8`
- Background: radial‑gradient `#f0f7f4` → `#cbdcd3`
- Glass: `rgba(255,255,255,0.75)` with `backdrop-filter: blur(20px)`

**Typography:**
- Headings: `'Lora', Georgia, serif`
- Body: `'Inter', -apple-system, sans-serif`
- Monospace: `'Consolas', 'Monaco', monospace`

**Layout:**
- Sticky header, responsive KPI bar, 12‑column CSS grid dashboard.

**Widgets:**
- Radar chart, AI reviewer panel, journal readiness cards, citation analytics, compliance audit grid, data provenance, improvement planner table.

**Interactivity:** hover effects, slide‑up transitions, loading skeletons, tooltips for provenance.

**Responsive:** desktop (>1200px), tablet (768–1199px), mobile (<768px).

---

## 7. Data Security & Privacy

- **Encryption:** HTTPS in transit; Supabase encrypts at rest; optionally AES‑256 for files.
- **Access control:** rate limiting (`slowapi`); JWT for future multi‑user; admin endpoints protected by API key.
- **Key management:** all keys in `.env`; never committed; rotation every 90 days.
- **Retention:** files deleted after 2h; task records after 1h; anonymized insights kept for benchmarking.
- **Privacy:** clear modal; user can request data deletion.
- **Secure coding:** Pydantic input validation; SQLAlchemy ORM; output escaping.

---

## 8. Error Handling & Resilience

- **Graceful degradation:** fallback values, partial results, warnings in UI.
- **Retries:** LLM – 5 retries (exponential backoff) with `tenacity`; external APIs – 3 retries; DB – 3 retries.
- **Timeouts:** LLM 45s, Crossref 10s, OpenAlex 15s, pipeline 5min.
- **Logging:** structured JSON with correlation IDs; Sentry for error tracking.
- **Circuit breaker:** after 3 external API failures, skip for 5min.
- **Error responses:** consistent JSON with HTTP status codes; user‑friendly frontend messages.

---

## 9. Provenance & Truthfulness Layer

**Every metric shows:**
- Metric name, value, formula/method, data sources, confidence level, timestamp, explanation.

**Implementation:**
- `ProvenanceEngine` class logs every computation into `provenance_log`.
- `manuscript_insights` stores list of provenance IDs.
- Frontend fetches provenance via `/api/provenance/{id}` and displays tooltips.

**Example metrics with provenance:**

| Metric | Formula / Method | Source | Confidence |
|--------|------------------|--------|------------|
| Readability | Flesch‑Kincaid | textstat | High |
| Plagiarism score | Cosine similarity | DuckDuckGo + embeddings | Medium |
| Journal fit | 0.6 semantic + 0.4 citedness | pgvector + OpenAlex | Medium |
| Trust score | sum(signals)/count(signals) | DOAJ, COPE, OASPA | High |
| Benchmark percentile | rank / sample_size | OpenAlex concept sample | Medium |
| LLM output | Structured prompt + Pydantic | NVIDIA NIM | Varies |

---

## 10. Unified Implementation Plan – Step by Step

### Phase 0 – Security, LLM & Provenance Prep (2 days)
- Rotate all API keys; store in `.env`; add to `.gitignore`.
- Modify `llm_client.py` to try NVIDIA first (`deepseek‑ai/deepseek‑v4‑flash`) with retry.
- Create `provenance_log` table and `ProvenanceEngine` class.
- Remove unused `router.py`.

### Phase 1 – Harden Module 1 (1 week)
- Add citation‑reference matching, duplicate detection, heading hierarchy, DOCX support, self‑citation.
- Store results in `manuscript_checks`; capture provenance for each check.

### Phase 2 – Data Infrastructure (3–4 days)
- Set up Supabase; run schema.
- Ingest journals from Crossref, OpenAlex, DOAJ; generate embeddings.

### Phase 3 – Trust Scorer (Module 3) (3–5 days)
- Scrape COPE/OASPA; import retraction data.
- Implement `/api/journals/trust` with provenance.

### Phase 4 – Journal Discovery (Module 2) (1 week)
- Implement `/api/journals/search` with pgvector; blend score; return provenance.

### Phase 5 – Statistical NLP & Semantic (Module 4) (1.5 weeks)
- Integrate `textstat`, `spaCy`, `wordfreq`, `KeyBERT`.
- Compute readability, passive voice, diversity, keywords; embed abstract.

### Phase 6 – Reference Resolution & Citation Network (1.5 weeks)
- Parse references; resolve via Crossref; cache in `resolved_references`.
- Fetch OpenAlex data; build citation graph with `networkx`.

### Phase 7 – Benchmark Pipeline (1 week)
- Nightly GitHub Action: sample OpenAlex papers per concept; store benchmarks.

### Phase 8 – UI Dashboard with Provenance (1 week)
- Extend frontend with all widgets; add provenance tooltips.
- Implement loading states, error handling.
- Update `exportPDFReport` to use real data and include methodology appendix.

### Phase 9 – Polish & Productionise (Ongoing)
- Add rate limiting; write tests; set up logging/monitoring; create `.env.example` and `README.md`; implement data deletion.

---

## 11. Additional Enhancements (Future)

- Plagiarism report with exact source URLs.
- 2‑level citation network.
- Author credibility score (opt‑in).
- Journal fit breakdown with reasoning.
- Reproducibility hash.
- Audit trail export (JSON).
- ORCID integration.
- User feedback loop for LLM outputs.
- Confidence intervals for percentiles.

---

## 12. Timeline & Resource Estimate

| Phase | Duration |
|-------|----------|
| 0 | 2 days |
| 1 | 1 week |
| 2 | 4 days |
| 3 | 4 days |
| 4 | 1 week |
| 5 | 1.5 weeks |
| 6 | 1.5 weeks |
| 7 | 1 week |
| 8 | 1 week |
| 9 | Ongoing |

**Total:** ~8–10 weeks part‑time. Zero infrastructure cost.

---

## 13. Immediate Next Steps

1. Rotate API keys and add them to `.env`.
2. Modify `llm_client.py` to use NVIDIA NIM first with retry.
3. Create the `provenance_log` table and `ProvenanceEngine`.
4. Set up Supabase project and run the schema.
5. Start coding Module 1 improvements with provenance capture.

---

## 14. Conclusion

This plan provides a complete, actionable roadmap to transform JournaBuddy from an MVP into a full‑featured research intelligence platform. By following the phases, you will achieve a modern, secure, transparent, and differentiated product—all with zero recurring costs.

**Now, let’s start building.**
