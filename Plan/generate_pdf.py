from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import datetime

# Setup document
doc = SimpleDocTemplate(
    "JournaBuddy_System_Design.pdf",
    pagesize=letter,
    rightMargin=60, leftMargin=60,
    topMargin=60, bottomMargin=40
)

styles = getSampleStyleSheet()

# Custom styles
title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1e3a8a'), spaceAfter=14, spaceBefore=10)
h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=15, textColor=colors.HexColor('#2563eb'), spaceAfter=10, spaceBefore=12)
h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#3b82f6'), spaceAfter=8, spaceBefore=10)
body = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=10)
code = ParagraphStyle('Code', parent=styles['Code'], fontSize=8, leading=11, leftIndent=8, rightIndent=8, spaceAfter=10, backColor=colors.HexColor('#f5f5f5'))
bullet = ParagraphStyle('Bullet', parent=body, leftIndent=20, spaceAfter=6)
cover_title = ParagraphStyle('CoverTitle', parent=styles['Title'], fontSize=36, textColor=colors.HexColor('#1e3a8a'), alignment=TA_CENTER, spaceAfter=16)
cover_sub = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#555555'), alignment=TA_CENTER, spaceAfter=10)
cover_small = ParagraphStyle('CoverSmall', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#777777'), alignment=TA_CENTER)

story = []

def p(text, style=body):
    story.append(Paragraph(text, style))

def pb():
    story.append(Spacer(1, 8))

def code_block(text):
    story.append(Preformatted(text, code))
    pb()

def table(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    pb()

# ==================== COVER ====================
story.append(Spacer(1, 200))
p("JournaBuddy", cover_title)
p("Full Open-Source System Design", cover_sub)
p("Production-Grade Architecture Using 100% Free & Open-Source Software", cover_small)
p(f"Generated: {datetime.datetime.now().strftime('%B %d, %Y')}", cover_small)
story.append(PageBreak())

# ==================== TOC ====================
p("Table of Contents", title)
toc_items = [
    "1. Technology Stack", "2. High-Level Architecture", "3. Component Deep Dive",
    "   3.1 FastAPI Application Server", "   3.2 Celery + Redis Task Queue",
    "   3.3 PostgreSQL + pgvector", "   3.4 MinIO Object Storage", "   3.5 Ollama LLM Cluster",
    "4. Real-Time Communication (SSE)", "5. Agent Orchestration Redesign",
    "6. Frontend Architecture", "7. Caching & Cost Optimization",
    "8. Security Model", "9. Monitoring & Observability",
    "10. Docker Compose Deployment", "11. Development Roadmap",
    "12. Hardware Requirements", "13. File Structure", "14. Summary of Key Improvements"
]
for item in toc_items:
    p(item, body)
story.append(PageBreak())

# ==================== 1. TECHNOLOGY STACK ====================
p("1. Technology Stack", title)
p("This architecture uses 100% free and open-source software. No API keys, no usage limits, no vendor lock-in.")
pb()

stack = [
    ["Layer", "Technology", "License", "Purpose"],
    ["Frontend", "React 19 + TypeScript + Vite", "MIT", "UI framework"],
    ["Styling", "TailwindCSS 4", "MIT", "Utility-first CSS"],
    ["Charts", "Apache ECharts", "Apache 2.0", "Interactive dashboards"],
    ["State", "Zustand", "MIT", "Global state management"],
    ["Query", "TanStack Query", "MIT", "Server state & caching"],
    ["Backend", "FastAPI (Python)", "MIT", "Async API server"],
    ["ORM", "SQLAlchemy 2 + Alembic", "MIT", "Database models & migrations"],
    ["Task Queue", "Celery", "BSD", "Distributed task processing"],
    ["Broker", "Redis", "BSD", "Celery broker & result backend"],
    ["Cache", "Redis", "BSD", "Response caching & rate limits"],
    ["Database", "PostgreSQL 16", "PostgreSQL", "Relational data"],
    ["Vectors", "pgvector", "MIT", "Embedding storage & search"],
    ["Object Store", "MinIO", "AGPLv3", "PDF storage (S3-compatible)"],
    ["LLM Inference", "Ollama", "MIT", "Local LLM serving"],
    ["Embeddings", "Sentence-Transformers", "Apache 2.0", "Text embeddings"],
    ["PDF Parsing", "pdfplumber + pymupdf", "MIT", "Text & layout extraction"],
    ["Gateway", "Nginx", "BSD", "Reverse proxy & static files"],
    ["Monitoring", "Prometheus + Grafana", "Apache 2.0", "Metrics & dashboards"],
    ["Logging", "Loki + Promtail", "AGPLv3", "Centralized log aggregation"],
    ["Tracing", "Jaeger", "Apache 2.0", "Distributed request tracing"],
    ["Container", "Docker + Docker Compose", "Apache 2.0", "Local dev & deployment"],
]
table(stack, [70, 130, 70, 130])
story.append(PageBreak())

# ==================== 2. HIGH-LEVEL ARCHITECTURE ====================
p("2. High-Level Architecture", title)

layers = [
    ("CLIENT LAYER", "Browser (React App) - Multiple concurrent users"),
    ("GATEWAY LAYER (Nginx)", "Static file serving, Reverse proxy to FastAPI, Rate limiting, SSL termination"),
    ("API LAYER (FastAPI)", "Async endpoints, JWT authentication, Pydantic v2 validation, SSE streaming, File upload handling"),
    ("DATA LAYER", "PostgreSQL + pgvector (relational + vector), Redis (Celery + Cache), MinIO (PDF Store)"),
    ("WORKER LAYER (Celery)", "PDF extraction tasks, Embedding generation, LLM agent tasks via Ollama, Convergence & aggregation"),
    ("INFERENCE LAYER (Ollama)", "Llama 3.1 8B, Mistral 7B, Nomic Embed - Load-balanced via Nginx upstream"),
]
for name, desc in layers:
    p(f"<b>{name}</b>", h3)
    p(desc, body)
story.append(PageBreak())

# ==================== 3. COMPONENT DEEP DIVE ====================
p("3. Component Deep Dive", title)

p("3.1 FastAPI Application Server", h2)
p("Why FastAPI over Flask/Django? Native async/await support is critical for SSE streaming and high-concurrency file uploads. Automatic OpenAPI/Swagger documentation. Pydantic v2 for strict request/response validation. Built-in dependency injection.", body)
code_block("""# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_pool = await create_pool()
    yield
    await app.state.redis_pool.close()

app = FastAPI(title="JournaBuddy API", lifespan=lifespan)
app.include_router(upload.router, prefix="/api")
app.include_router(stream.router, prefix="/api")""")
p("Why async matters: File uploads are I/O bound. With sync workers, each upload blocks a process. With FastAPI + Uvicorn, one process handles hundreds of concurrent uploads.", body)

p("3.2 Celery + Redis Task Queue", h2)
p("Redis acts as both message broker and result backend. Celery workers run in separate containers, horizontally scalable. Flower provides web UI for task inspection.", body)
code_block("""# app/worker/celery_app.py
from celery import Celery

celery_app = Celery(
    "journabuddy",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1"
)

celery_app.conf.task_routes = {
    "app.worker.tasks.extract_pdf": {"queue": "io_bound"},
    "app.worker.tasks.run_agent": {"queue": "llm_bound"},
}""")
p("Separate queues allow different scaling policies: io_bound (2-4 workers), cpu_bound (2 workers), llm_bound (3-5 workers).", body)
code_block("""# Chord for dependent agents
from celery import chord, chain

workflow = chord(parallel_group)(
    chain(
        run_truth_checker.s(task_id),
        run_quality_checker.s(task_id),
        converge_results.s(task_id)
    )
)""")
p("Key advantage: If a worker crashes mid-task, Celery automatically re-queues the task to another worker. No lost tasks.", body)

p("3.3 PostgreSQL + pgvector", h2)
p("Why pgvector instead of a separate vector DB? One less service to operate. ACID transactions across relational + vector data. Backup/restore is unified. FOSS and battle-tested.", body)
code_block("""-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    dashboard_payload JSONB,
    progress_percent INTEGER DEFAULT 0
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB
);

CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);""")

p("3.4 MinIO Object Storage", h2)
p("Why MinIO? Drop-in S3 replacement, fully S3-API compatible. Single binary, runs in Docker with one command. Erasure coding for data durability. FOSS (AGPLv3).", body)
code_block("""import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    config=Config(signature_version="s3v4"),
)""")

p("3.5 Ollama LLM Cluster", h2)
p("Why Ollama? Single command model management. REST API compatible with OpenAI API format. Runs on CPU (slow but free) or GPU (fast). Supports model quantization.", body)

models = [
    ["Model", "Size", "Role", "RAM Needed"],
    ["llama3.1:8b", "8B", "General reasoning, all agents", "~6 GB"],
    ["mistral:7b", "7B", "Fast fallback, proofreading", "~5 GB"],
    ["nomic-embed-text", "137M", "Document embeddings", "~300 MB"],
]
table(models, [100, 60, 160, 80])
p("Load balancing: Run 3 Ollama instances behind Nginx upstream. Celery workers round-robin across them.", body)
code_block("""upstream ollama_cluster {
    least_conn;
    server ollama-1:11434 max_fails=3 fail_timeout=30s;
    server ollama-2:11434 max_fails=3 fail_timeout=30s;
    server ollama-3:11434 max_fails=3 fail_timeout=30s;
}""")
story.append(PageBreak())

# ==================== 4. SSE ====================
p("4. Real-Time Communication: Server-Sent Events (SSE)", title)
p("Replace polling with SSE. The frontend opens one persistent HTTP connection. The backend pushes updates as agents complete.", body)
code_block("""# FastAPI SSE endpoint
@router.get("/stream/{task_id}")
async def stream_task(task_id: str):
    return StreamingResponse(
        event_stream(task_id, redis),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )""")
code_block("""# Celery worker publishes events
def publish_agent_complete(task_id, agent_name, result):
    redis.publish(f"task:{task_id}", json.dumps({
        "type": "agent_complete",
        "agent": agent_name,
        "result": result
    }))""")
code_block("""// Frontend React hook
export function useTaskStream(taskId: string) {
  const [agents, setAgents] = useState({});
  useEffect(() => {
    const es = new EventSource(`/api/stream/${taskId}`);
    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'agent_complete') {
        setAgents(prev => ({ ...prev, [data.agent]: data.result }));
      }
    };
    return () => es.close();
  }, [taskId]);
  return { agents };
}""")
story.append(PageBreak())

# ==================== 5. AGENT ORCHESTRATION ====================
p("5. Agent Orchestration Redesign", title)
p("Problem with original design: 11 separate LLM calls = 11x latency + 11x context window overhead.", body)
p("Optimized agent grouping (7 calls instead of 11, better context sharing):", body)

p("Phase 1: Extraction (I/O bound)", h3)
p("extract_pdf() -> raw text -> chunk_and_embed() -> vector store", body)

p("Phase 2: Parallel Agent Execution (LLM bound) - Celery Group", h3)
agents = [
    "Agent Group A: Document Intelligence -> {title, authors, abstract, keywords, topics, category}",
    "Agent Group B: Language & Compliance -> {grammar_issues[], citation_format, missing_citations[], style_score}",
    "Agent Group C: Originality Analysis -> {plagiarism_risk, novelty_score, similar_papers[], red_flags[]}",
    "Agent Group D: Research Rigor -> {methodology_score, flaws[], strengths[], statistical_validity}",
    "Agent Group E: Submission Readiness -> {readiness_score, missing_elements[], journal_fit[], recommendations[]}",
    "Agent Group F: Peer Review Simulation -> {reviewer_1, reviewer_2, reviewer_3} (3 personas in one call)",
]
for a in agents:
    p(f"• {a}", bullet)

p("Phase 3: Dependent Agents (Celery Chain)", h3)
p("Truth Checker: Input = Group B (citations) + Group C (novelty claims). Verifies: Do citations support claims? Output = {verified_claims[], disputed_claims[], confidence}", body)
p("Quality Checker: Input = Truth Checker output + Group C output. Evaluates: Overall research integrity. Output = {quality_score, risk_level, critical_issues[]}", body)

p("Phase 4: Convergence", h3)
p("assemble_dashboard() -> JSON payload", body)

p("Why this grouping works: Agents within a group share the same input context, reducing redundant token usage. Groups A-F run truly in parallel (6 concurrent LLM calls). Dependent agents only run after prerequisites finish. Total LLM calls per paper: ~8 instead of 13.", body)
story.append(PageBreak())

# ==================== 6. FRONTEND ====================
p("6. Frontend Architecture", title)
p("Tech Stack:", h3)
for t in ["Vite - Build tool, faster than CRA, native ESM", "React 19 - Concurrent features, automatic batching",
          "TanStack Query - Caching, background refetching, deduplication", "Zustand - Lightweight global state",
          "TailwindCSS - Utility styling", "Apache ECharts - Interactive charts (radar, gauge, timeline)",
          "React-PDF - PDF preview with highlighted sections"]:
    p(f"• {t}", bullet)

p("Component Hierarchy:", h3)
code_block("""App
├── Layout (Sidebar + Header)
│   ├── UploadPage -> DropZone -> redirect to /tasks/{id}
│   ├── TaskListPage -> TaskCard[] (infinite scroll)
│   └── DashboardPage (/tasks/:taskId)
│       ├── TaskHeader (status badge + progress)
│       ├── PDFViewer (side-by-side with highlights)
│       ├── AgentGrid
│       │   ├── MetadataCard
│       │   ├── ReadinessScore (Gauge chart)
│       │   ├── QualityRadar (Radar chart)
│       │   ├── ReviewerPanel (Accordion)
│       │   ├── CitationChecker (Table)
│       │   └── PlagiarismReport (Heatmap)
│       └── ExportPanel (PDF/JSON download)""")

p("State Management Strategy:", h3)
p("• Server state (tasks, agent results) -> TanStack Query (caches by task_id, auto-refetches on window focus)", bullet)
p("• Client state (selected agent, UI theme) -> Zustand", bullet)
p("• Ephemeral state (SSE connection, upload progress) -> Local component state", bullet)
story.append(PageBreak())

# ==================== 7. CACHING ====================
p("7. Caching & Cost Optimization", title)

p("7.1 Content-Addressable Cache", h2)
p("Hash the extracted text. If the same paper is uploaded twice, return cached results instantly.", body)
code_block("""import hashlib

def get_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

cached_task = db.query(Task).filter(Task.content_hash == hash).first()
if cached_task and cached_task.status == "completed":
    return cached_task.dashboard_payload  # Instant response""")

p("7.2 Embedding Cache", h2)
p("Embeddings are deterministic. Cache them by chunk content hash:", body)
code_block("""cache_key = f"emb:{chunk_hash}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)
embedding = model.encode(chunk_text)
redis.setex(cache_key, 86400 * 30, json.dumps(embedding.tolist()))""")

p("7.3 LLM Response Cache", h2)
p("For deterministic prompts (metadata extraction), cache LLM responses:", body)
code_block("""prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
cache_key = f"llm:{model}:{prompt_hash}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)
response = call_ollama(prompt)
redis.setex(cache_key, 86400 * 7, json.dumps(response))""")

p("7.4 Estimated Savings", h2)
savings = [
    ["Cache Type", "Savings", "Description"],
    ["Duplicate papers", "100%", "Return instantly"],
    ["Embedding cache", "~30%", "On re-uploads"],
    ["LLM cache", "~15%", "On similar document types"],
]
table(savings, [120, 80, 200])
story.append(PageBreak())

# ==================== 8. SECURITY ====================
p("8. Security Model", title)
p("8.1 Authentication", h2)
p("• JWT tokens (access token: 15min, refresh token: 7 days)", bullet)
p("• bcrypt for password hashing", bullet)
p("• OAuth2 optional (GitHub/Google login)", bullet)

p("8.2 Authorization", h2)
p("• Row-level security: Users can only access tasks where user_id = current_user.id", bullet)
p("• API endpoints validate ownership on every request", bullet)

p("8.3 Input Sanitization", h2)
p("• File size limit: 50MB max", bullet)
p("• Page limit: 200 pages max (configurable)", bullet)
p("• PDF sandboxing: Extract text inside a Docker container with no network access", bullet)
p("• Content validation: Reject non-PDF MIME types at Nginx level", bullet)

p("8.4 Data Privacy", h2)
p("• All processing is on-premise - no data leaves your servers", bullet)
p("• Vector embeddings and LLM inputs never touch third-party APIs", bullet)
p("• MinIO buckets are private by default", bullet)
story.append(PageBreak())

# ==================== 9. MONITORING ====================
p("9. Monitoring & Observability", title)
p("9.1 Metrics (Prometheus)", h2)
code_block("""# Custom metrics
TASKS_CREATED = Counter(
    'journabuddy_tasks_created_total', 'Total tasks'
)
AGENT_LATENCY = Histogram(
    'journabuddy_agent_duration_seconds',
    'Agent latency', ['agent_name']
)
LLM_TOKENS = Counter(
    'journabuddy_llm_tokens_total',
    'Tokens consumed', ['model']
)""")

p("9.2 Logging (Loki)", h2)
p("Structured JSON logs from every component.", body)
code_block("""{
  "timestamp": "2026-07-29T10:30:00Z",
  "level": "INFO",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent": "citation_checker",
  "event": "agent_started",
  "input_tokens": 4500
}""")

p("9.3 Tracing (Jaeger)", h2)
p("Trace a task through the entire pipeline. Key insight: Tracing reveals that Agent Group B (Language & Compliance) is the bottleneck at 12.1s. You can then optimize its prompt or assign it to a faster Ollama instance.", body)
story.append(PageBreak())

# ==================== 10. DOCKER COMPOSE ====================
p("10. Docker Compose Deployment", title)
code_block("""version: "3.8"

services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/journabuddy
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000

  worker-io:
    build: ./backend
    command: celery -A app.worker.celery_app worker -Q io_bound -c 4

  worker-llm:
    build: ./backend
    command: celery -A app.worker.celery_app worker -Q llm_bound -c 3

  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: journabuddy

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"

  ollama-1:
    image: ollama/ollama

  prometheus:
    image: prom/prometheus

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]""")
story.append(PageBreak())

# ==================== 11. ROADMAP ====================
p("11. Development Roadmap", title)

roadmap = [
    ("Phase 1: Foundation (Week 1-2)", [
        "Docker Compose setup with all services",
        "FastAPI skeleton + PostgreSQL + pgvector",
        "MinIO integration for file storage",
        "Basic PDF extraction (pdfplumber)",
        "React frontend with upload + task list",
    ]),
    ("Phase 2: Core Pipeline (Week 3-4)", [
        "Celery + Redis task queue",
        "Semantic chunking + sentence-transformers embeddings",
        "Ollama integration with llama3.1:8b",
        "6 parallel agent groups implementation",
    ]),
    ("Phase 3: Real-time & UX (Week 5)", [
        "SSE streaming endpoint",
        "Frontend dashboard with progressive loading",
        "Agent result cards with ECharts visualizations",
        "Error boundaries + graceful degradation",
    ]),
    ("Phase 4: Intelligence (Week 6)", [
        "Dependent agents (Truth Checker, Quality Checker)",
        "Vector similarity search for plagiarism",
        "Convergence engine (BI Dashboard Payload assembly)",
        "Content-addressable caching",
    ]),
    ("Phase 5: Production Hardening (Week 7-8)", [
        "JWT authentication + user management",
        "Nginx reverse proxy + SSL",
        "Prometheus + Grafana monitoring",
        "Loki logging + Jaeger distributed tracing",
        "Rate limiting + input validation",
        "Backup strategy (PostgreSQL dumps + MinIO versioning)",
    ]),
]
for phase, items in roadmap:
    p(phase, h3)
    for item in items:
        p(f"[ ] {item}", bullet)
    pb()
story.append(PageBreak())

# ==================== 12. HARDWARE ====================
p("12. Hardware Requirements", title)
hw = [
    ["Deployment", "CPU", "RAM", "Storage", "GPU"],
    ["Development (1 user)", "4 cores", "16 GB", "50 GB SSD", "Optional"],
    ["Small Team (5-10 users)", "8 cores", "32 GB", "200 GB SSD", "RTX 3060 12GB"],
    ["Production (50+ users)", "16+ cores", "64 GB", "1 TB NVMe", "RTX 4090 24GB"],
]
table(hw, [110, 60, 60, 80, 90])
p("CPU-only is viable: llama3.1:8b on CPU processes ~5-10 tokens/sec. A full agent run takes ~30-60 seconds instead of 5-10 seconds on GPU. For development and small teams, this is acceptable.", body)
story.append(PageBreak())

# ==================== 13. FILE STRUCTURE ====================
p("13. File Structure", title)
code_block("""journabuddy/
├── docker-compose.yml
├── nginx.conf
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── events.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── upload.py
│   │   │   ├── status.py
│   │   │   └── stream.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── storage.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   └── vector_store.py
│   │   └── worker/
│   │       ├── celery_app.py
│   │       ├── tasks.py
│   │       └── agents/
│   │           ├── document_intelligence.py
│   │           ├── language_compliance.py
│   │           ├── originality.py
│   │           ├── research_rigor.py
│   │           ├── readiness.py
│   │           ├── peer_review.py
│   │           ├── truth_checker.py
│   │           └── quality_checker.py
│   └── alembic/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── stores/
│       └── lib/
└── monitoring/
    ├── prometheus.yml
    ├── grafana-dashboards/
    └── loki-config.yml""")
story.append(PageBreak())

# ==================== 14. SUMMARY ====================
p("14. Summary of Key Improvements", title)
p("This table compares the original JournaBuddy design against the new open-source architecture:", body)

summary = [
    ["Aspect", "Original", "New Design"],
    ["Frontend updates", "Polling every 2s", "SSE push (instant)"],
    ["Workers", "In-process ThreadPool", "Celery + Redis (distributed, persistent)"],
    ["Database", "SQLite", "PostgreSQL + pgvector (ACID, scalable)"],
    ["Vector store", "Local file", "pgvector (unified with relational data)"],
    ["LLM API", "External paid API", "Ollama (local, free, private)"],
    ["Agent calls", "11 separate LLM calls", "6 grouped parallel + 2 dependent = 8 total"],
    ["Error handling", "All-or-nothing", "Per-agent error boundaries"],
    ["Results", "Big-bang at end", "Progressive streaming as each agent finishes"],
    ["Monitoring", "None", "Prometheus + Grafana + Jaeger + Loki"],
    ["Caching", "None", "3-layer cache (content, embedding, LLM)"],
    ["Deployment", "Manual", "Docker Compose (one command)"],
]
table(summary, [90, 120, 160])

p("This architecture is designed to be deployed entirely on-premise with zero external API dependencies. Every component is free, open-source, and production-ready. The system scales horizontally by adding more Celery workers and Ollama instances behind the Nginx load balancer.", body)

# Build PDF
doc.build(story)
print("PDF generated successfully: JournaBuddy_System_Design.pdf")