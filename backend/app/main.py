"""
JournaBuddy FastAPI Application Entry Point
Configures the application, registers all API routers, sets up CORS middleware,
and verifies the database connection on startup.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import upload, task, report
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs startup checks (DB connectivity) before accepting requests.
    Runs cleanup on shutdown.
    """
    # ── Startup: verify database connection ──
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully.")
    except Exception as e:
        logger.warning(f"Database not yet available on startup: {e}")
        # Non-fatal: DB may still be initializing; connections will be retried per-request

    yield

    # ── Shutdown: dispose connection pool ──
    from app.db.session import engine
    await engine.dispose()
    logger.info("Database connection pool disposed.")


# Initialize FastAPI application
app = FastAPI(
    title="JournaBuddy API",
    description=(
        "Backend API for the JournaBuddy Research Paper Intelligence Platform. "
        "Provides PDF analysis, semantic chunking, LLM agent evaluation, "
        "and provenance-tracked scientific manuscript scoring."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiting ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Prometheus Metrics ──
Instrumentator().instrument(app).expose(app)

# ── CORS Middleware ──
# In production, replace '*' with the actual frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API Routers ──
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(task.router, prefix="/api", tags=["Task Status"])
app.include_router(report.router, prefix="/api", tags=["Report"])


# ── Health Check Endpoints ──
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Simple liveness probe — returns ok if the API server is running."""
    return {"status": "ok", "version": "2.0.0"}
