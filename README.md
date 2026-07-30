# JournaBuddy – Research Paper Intelligence Platform

**JournaBuddy** is an advanced, AI-driven manuscript evaluation platform designed to radically optimize, benchmark, and secure scientific manuscripts prior to journal submission. 

By combining **rigorous mathematical NLP**, **semantic LLM peer-review evaluations**, and a **predictive logistic regression model**, JournaBuddy provides unmatched transparency, automated feedback, and high-precision journal matching.

---

## 🌟 Core Modules

JournaBuddy answers the most critical questions for scientific authors:

### 1. Is my paper academically rigorous? (*Mathematical NLP & Readability Engine*)
We discarded fragile grade-school formulas for rigorous Information Theory mathematics:
*   **Shannon Entropy:** Calculates the true information density and vocabulary distribution unpredictability.
*   **Simpson's Diversity Index:** Mathematically detects vocabulary repetition and fluff.
*   **Coleman-Liau Index:** A PDF-safe grade level metric based strictly on character ratios.
*   **TF-IDF Keyword Extraction:** Mathematically identifies the most significant terms in the paper.

### 2. Is my paper original? (*Internal Plagiarism Checker*)
*   Uses `pgvector` to cross-reference every sentence of the uploaded manuscript against a massive PostgreSQL database of all previously uploaded documents using a `CROSS JOIN LATERAL` query. 
*   Flags plagiarized sentences with exact similarity percentages and cites the source filename.

### 3. Will my paper be accepted? (*Logistic Regression Prediction Model*)
*   Instead of naive guesses, JournaBuddy uses a **Logistic Regression Sigmoid** algorithm ($P = 1 / (1 + e^{-z})$).
*   Dynamically calculates Acceptance Likelihood by weighting semantic compatibility (40%), AI Methodological Rigor (30%), Language Density (15%), and Novelty (15%).

### 4. What do the reviewers think? (*AI Peer Review Simulation*)
*   Runs an asynchronous cascade of AI Agents (Strict Methodologist, Domain Specialist, Copy Editor).
*   Powered by local **Ollama (`Llama 3.1:8b`)** with dynamic fallbacks to NVIDIA NIM and OpenAI APIs.

### 5. Which journals fit my paper? (*Semantic Matching & Discovery*)
*   Embeds the manuscript using `sentence-transformers` and performs Cosine Similarity matching against indexed journal aims & scopes using PostgreSQL `pgvector`.
*   Cross-checks journals against DOAJ, COPE, and OpenAlex for trust scores.

---

## 🚀 Key Production Capabilities

*   **Dynamic PDF Proof Certificates:** Automatically generates stunning, downloadable PDF reports featuring **ReportLab Vector Graphics** (5-axis Radar Charts for AI reviews, Bar Charts for Journal Matches, and Plagiarism Alerts).
*   **Interactive Glassmorphism Dashboard:** Real-time progress tracking, Server-Sent Events (SSE), and a modern React UI.
*   **Asynchronous Celery Architecture:** Non-blocking processing pipelines powered by Celery worker pools and a Redis message broker.

---

## 🏗️ System Architecture & Tech Stack

```
[ Client Layer (React 19 + Vite + TailwindCSS) ]
                     │ (HTTP / SSE)
                     ▼
[ API Layer (FastAPI Async Server) ]
       │             │             │
       ▼             ▼             ▼
[ PostgreSQL ]  [ Redis ]    [ MinIO ]
 (pgvector)    (Broker/Cache) (PDF Store)
                     │
                     ▼
[ Worker Layer (Celery Background Workers) ]
                     │
                     ▼
[ Inference Layer (Local Ollama LLMs) ]
```

*   **Frontend:** React 19 + TypeScript + Vite, TailwindCSS (Glassmorphism UI), Apache ECharts.
*   **API Gateway:** FastAPI async API server.
*   **Database & Vectors:** PostgreSQL 16 with `pgvector` extension (`vector(384)`).
*   **Object Store:** MinIO (S3-compatible private PDF binary storage).
*   **Task Queue & Cache:** Celery 5 worker pools with Redis 7 message broker and SSE Pub/Sub.
*   **Local Inference:** Ollama serving `Llama 3.1:8b` and `sentence-transformers` (`all-MiniLM-L6-v2`).
*   **PDF Generation:** `reportlab` with native vector graphics (`reportlab.graphics`).

---

## 📖 Documentation & System Reports

For complete details on the architecture design, database schemas, data pipelines, and implementation phases, refer to our master documentation:
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
│   │   ├── db/               # Database Sessions & Alembic Migrations
│   │   ├── models/           # SQLAlchemy Models (tasks, chunks, provenance, journals)
│   │   ├── services/         # Plagiarism, AI Agents, NLP Math, Journal Matching
│   │   └── worker/           # Celery Task Definitions
│   └── Dockerfile            # Multi-stage Python Container Dockerfile
├── frontend/                 # React 19 + TypeScript + Vite Application
│   └── src/
│       ├── components/       # Reusable Glassmorphism UI & Chart Components
│       ├── hooks/            # Custom React & SSE Hooks
│       └── services/         # API Client Services
├── docs/                     # System Documentation (Plans, Reports, Rules)
├── test_cases/               # Step-by-Step Testing Suites
├── data/                     # Sample Research PDFs
├── docker-compose.yml        # Multi-Container Orchestration Manifest
└── scripts/run_podman.bat    # 1-Click Windows Startup Script
```

---

## 🛠️ Getting Started (Local Deployment)

### Prerequisites
*   **Podman Desktop** (or Docker Desktop) installed and running.
*   Git installed.

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
*   **Frontend Web App:** `http://localhost`
*   **FastAPI Backend API:** `http://localhost:8000/api` (Swagger Docs: `http://localhost:8000/docs`)
*   **MinIO Object Store Dashboard:** `http://localhost:9001` (User: `minioadmin` | Pass: `minioadmin`)

---

## 🧪 Testing & Verification

JournaBuddy uses phase-by-phase test suites located in the `test_cases/` folder.
Run API health check manually:
```bash
curl http://localhost:8000/health
```

---

## 👤 Author & Attribution

**Abdullah Al Mamun**  
*BSc, MSc - Software Engineering*  
TU Wien (Vienna, Austria) & Daffodil International University  
*   **Email:** [mamun.swe.de@gmail.com](mailto:mamun.swe.de@gmail.com)  
*   **GitHub:** [@abbysweb](https://github.com/abbysweb)  
*   **ORCID:** [0009-0006-7473-0024](https://orcid.org/0009-0006-7473-0024)

---

## 📄 License

Licensed under the open-source **MIT License**.
