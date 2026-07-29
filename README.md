# JournaBuddy – Research Paper Intelligence Platform

**JournaBuddy** is an open-source, hybrid AI platform designed to evaluate, optimize, and benchmark scientific manuscripts prior to journal submission. 

By combining **symbolic rule checks**, **statistical NLP**, and **semantic LLM agent evaluations**, JournaBuddy provides radical transparency, mathematical provenance, and automated peer-review feedback with zero vendor lock-in.

---

## 🌟 Core Features & Answers Provided

JournaBuddy answers four core questions for scientific authors:

1. **Is my paper ready to submit?** (*Module 1: Manuscript Readiness Checker*)
   * Evaluates section completeness, acronym resolution, reference-citation linking, and grammar.
2. **Which journals fit my paper?** (*Module 2: Journal Discovery & Matching*)
   * Matches abstract & paper embeddings against target journal scopes using `pgvector` cosine similarity.
3. **Are those journals trustworthy?** (*Module 3: Journal Trust Scorer*)
   * Cross-checks journal metrics against DOAJ, COPE, and OpenAlex indexing signals.
4. **How does my paper compare to its field?** (*Module 4: BI Dashboard & Benchmarking*)
   * Provides Flesch-Kincaid readability metrics, passive voice density, jargon heatmaps, and field-normalized percentiles.

---

## 🚀 Key Production Capabilities

* **3-Persona AI Peer Review Simulation:** Generates detailed reports from 3 AI reviewer personas (Strict Methodologist, Domain Specialist, Copy Editor).
* **Interactive Bounding Box PDF Annotations:** Clicking any extracted suggestion highlights the exact paragraph coordinates directly on the PDF canvas.
* **BibTeX Auto-Fixer & 2D/3D Citation Graph:** Resolves missing DOIs via Crossref and visualizes citation networks using `vis-network`.
* **Radical Transparency & Provenance Logging:** Every score is linked to a mathematical formula and logged in `provenance_log`.
* **Multi-Tier Fallback Cascade:** Local inference via Ollama (`Llama 3.1:8b`) with automatic fallbacks to NVIDIA NIM, Gemini, or OpenAI APIs.

---

## 🏗️ System Architecture & Tech Stack

```
[ Client Layer (React 19 + Vite) ]
             │ (HTTP / SSE)
             ▼
[ Reverse Proxy (Nginx Gateway) ]
             │
             ▼
[ API Layer (FastAPI Async Server) ]
      │             │             │
      ▼             ▼             ▼
[ PostgreSQL ]  [ Redis ]    [ MinIO ]
 (pgvector)    (Broker/Cache) (PDF Store)
                    │
                    ▼
[ Worker Layer (Celery Workers) ]
                    │
                    ▼
[ Inference Layer (Local Ollama LLMs) ]
```

* **Frontend:** React 19 + TypeScript + Vite, TailwindCSS (Glassmorphism UI), Apache ECharts, `vis-network`.
* **API Gateway:** Nginx reverse proxy + FastAPI async API server.
* **Database & Vectors:** PostgreSQL 16 with `pgvector` extension (`vector(384)`).
* **Object Store:** MinIO (S3-compatible private PDF binary storage).
* **Task Queue & Cache:** Celery 5 worker pools with Redis 7 message broker and SSE Pub/Sub.
* **Local Inference:** Ollama serving `Llama 3.1:8b` and `sentence-transformers` (`all-MiniLM-L6-v2`).

---

## 📖 Documentation & System Reports

For complete details on the architecture design, database schemas, 8-step data pipeline, error handling strategies, and implementation phases, refer to our master documentation and dynamic reports:
* 📘 **Master Implementation Plan:** [docs/planning/plan.md](docs/planning/plan.md)
* 📄 **System Report (LaTeX Source):** [docs/reports/system_report.tex](docs/reports/system_report.tex)
* 📕 **System Report (Compiled PDF):** [docs/reports/system_report.pdf](docs/reports/system_report.pdf)

---

## 📁 Repository Structure

```
JournaBuddy/
├── backend/                  # FastAPI Application & Celery Worker Logic
│   ├── app/
│   │   ├── api/              # API Route Handlers (/upload, /health, /stream)
│   │   ├── core/             # Core Settings & Security Configuration
│   │   ├── db/               # Database Sessions & Alembic Migrations
│   │   ├── models/           # SQLAlchemy Models (tasks, chunks, provenance, journals)
│   │   ├── schemas/          # Pydantic Request & Response Schemas
│   │   ├── services/         # Extraction & NLP Logic (pdfplumber, textstat)
│   │   └── worker/           # Celery Task Definitions & App Config
│   └── Dockerfile            # Multi-stage Python Container Dockerfile
├── frontend/                 # React 19 + TypeScript + Vite Application
│   └── src/
│       ├── components/       # Reusable Glassmorphism UI & Chart Components
│       ├── hooks/            # Custom React & SSE Hooks
│       ├── services/         # API Client Services & Network Connections
│       └── types/            # TypeScript Interfaces & Types
├── docs/                     # System Documentation
│   ├── planning/             # Complete System Plan & Master Roadmap (docs/planning/plan.md)
│   ├── reports/              # Diagnostic Reports & Benchmarks
│   └── internal/             # Local Rules & Project Guidelines
├── test_cases/               # Step-by-Step Testing & Verification Suites
├── scripts/                  # Diagnostics & Verification Helper Scripts
├── data/                     # Sample Research PDFs & BibTeX Files
├── monitoring/               # Prometheus & Grafana Configuration Files
├── docker-compose.yml        # Multi-Container Orchestration Manifest
├── nginx.conf                # Nginx Gateway Proxy Configuration
└── run.bat                   # 1-Click Windows Startup Script
```

---

## 🛠️ Getting Started (Local Deployment)

### Prerequisites
* **Podman Desktop** (or Docker Desktop) installed and running.
* Git installed.

### Quick Start (1-Click Startup)

**For Podman Desktop Users:**
Run the Podman batch launcher:
```cmd
scripts\run_podman.bat
```
Or run Podman Compose manually:
```bash
podman compose up -d --build
```

**For Docker Desktop Users:**
```bash
docker-compose up -d --build
```

Access the services:
* **Frontend Web App:** `http://localhost`
* **FastAPI Backend API:** `http://localhost:8000/api` (Swagger Docs: `http://localhost:8000/docs`)
* **MinIO Object Store Dashboard:** `http://localhost:9001` (User: `minioadmin` | Pass: `minioadmin`)

---

## 🧪 Testing & Verification

JournaBuddy uses phase-by-phase test suites located in the `test_cases/` folder:
* **Phase 1 Verification:** Refer to [test_cases/phase_1_verification.md](test_cases/phase_1_verification.md) to test container initialization, MinIO uploads, and API health.

Run API health check manually:
```bash
curl http://localhost:8000/health
```

---

## 👤 Author & Attribution

**Abdullah Al Mamun**  
*BSc, MSc - Software Engineering*  
TU Wien (Vienna, Austria) & Daffodil International University  
* **Email:** [mamun.swe.de@gmail.com](mailto:mamun.swe.de@gmail.com)  
* **GitHub:** [@abbysweb](https://github.com/abbysweb)  
* **ORCID:** [0009-0006-7473-0024](https://orcid.org/0009-0006-7473-0024)

---

## 📄 License

Licensed under the open-source **MIT License**.
