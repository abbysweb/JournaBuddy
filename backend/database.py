import os
import json
import time
from sqlalchemy import create_engine, Column, String, Float, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://journabuddy:secretpassword@db:5432/journabuddy')

try:
    if DATABASE_URL.startswith("postgresql"):
        # Test connection with a short timeout to prevent hanging on startup
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 3})
        conn = engine.connect()
        conn.close()
        print("[Database] Connected to PostgreSQL successfully.")
    else:
        raise ValueError("Not a PostgreSQL connection string.")
except Exception as e:
    print(f"[Database] PostgreSQL connection failed ({e}). Falling back to local SQLite.")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'journabuddy.db'))
    DATABASE_URL = f"sqlite:///{db_path}"
    # SQLite needs special config for multi-threading in Flask dev mode
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="processing")
    current_agent = Column(String, nullable=True)
    completed_agents = Column(Text, default="[]")  # Stored as JSON string
    result = Column(Text, nullable=True)          # Stored as JSON string
    error = Column(Text, nullable=True)
    timestamp = Column(Float, default=time.time)

class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    issn = Column(String, index=True, nullable=True)
    eissn = Column(String, nullable=True)
    title = Column(String, nullable=False)
    publisher = Column(String, nullable=True)
    openalex_id = Column(String, nullable=True)
    is_oa = Column(Boolean, default=False)
    scope_description = Column(Text, nullable=True)
    scope_embedding = Column(Text, nullable=True)  # JSON serialized array of floats
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)

class JournalMetric(Base):
    __tablename__ = "journal_metrics"

    journal_id = Column(Integer, ForeignKey("journals.id"), primary_key=True)
    year = Column(Integer, primary_key=True)
    works_count = Column(Integer, nullable=True)
    cited_by_count = Column(Integer, nullable=True)
    h_index = Column(Integer, nullable=True)
    two_yr_mean_citedness = Column(Float, nullable=True)

class JournalTrustFlag(Base):
    __tablename__ = "journal_trust_flags"

    journal_id = Column(Integer, ForeignKey("journals.id"), primary_key=True)
    in_doaj = Column(Boolean, default=False)
    doaj_seal = Column(Boolean, default=False)
    cope_member = Column(Boolean, default=False)
    oaspa_member = Column(Boolean, default=False)
    retraction_count = Column(Integer, default=0)
    last_checked = Column(Float, default=time.time)

class ResolvedReference(Base):
    __tablename__ = "resolved_references"

    id = Column(Integer, primary_key=True, index=True)
    raw_citation_text = Column(Text, nullable=True)
    doi = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    venue_type = Column(String, nullable=True)
    openalex_id = Column(String, nullable=True)
    cited_by_count = Column(Integer, nullable=True)
    concepts = Column(Text, nullable=True)  # JSON string
    resolved_at = Column(Float, default=time.time)

class ManuscriptInsight(Base):
    __tablename__ = "manuscript_insights"

    manuscript_check_id = Column(String, primary_key=True, index=True)  # maps to task_id
    readability = Column(Text, nullable=True)  # JSON string
    citation_analytics = Column(Text, nullable=True)  # JSON string
    topic_analytics = Column(Text, nullable=True)  # JSON string
    benchmark_comparison = Column(Text, nullable=True)  # JSON string
    provenance_ids = Column(Text, nullable=True)  # JSON string
    computed_at = Column(Float, default=time.time)

class FieldBenchmark(Base):
    __tablename__ = "field_benchmarks"

    openalex_concept_id = Column(String, primary_key=True, index=True)
    concept_name = Column(String, nullable=True)
    avg_word_count = Column(Float, nullable=True)
    avg_reference_count = Column(Float, nullable=True)
    avg_reference_recency_years = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    computed_at = Column(Float, default=time.time)

class ProvenanceLog(Base):
    __tablename__ = "provenance_log"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, index=True, nullable=True)
    metric_name = Column(String, nullable=True)
    metric_value = Column(Text, nullable=True)  # JSON string
    formula = Column(Text, nullable=True)
    data_sources = Column(Text, nullable=True)  # JSON string list
    confidence_level = Column(String, nullable=True)
    timestamp = Column(Float, default=time.time)
    raw_data_snapshot = Column(Text, nullable=True)  # JSON string
    explanation = Column(Text, nullable=True)

# Create all tables on initialization/import
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_task(task_id: str):
    db = SessionLocal()
    new_task = Task(
        task_id=task_id,
        status='processing',
        current_agent=None,
        completed_agents='[]',
        result=None,
        error=None,
        timestamp=time.time()
    )
    db.add(new_task)
    db.commit()
    db.close()

def get_task(task_id: str) -> dict:
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()
    db.close()
    if task:
        return {
            'task_id': task.task_id,
            'status': task.status,
            'current_agent': task.current_agent,
            'agents_completed': json.loads(task.completed_agents) if task.completed_agents else [],
            'result': json.loads(task.result) if task.result else None,
            'error': task.error,
            'timestamp': task.timestamp
        }
    return None

def update_task_status(task_id: str, status: str, current_agent: str = None, error: str = None):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        task.status = status
        task.current_agent = current_agent
        task.error = error
        db.commit()
    db.close()

def update_task_agent_complete(task_id: str, agent_name: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        completed = json.loads(task.completed_agents) if task.completed_agents else []
        if agent_name not in completed:
            completed.append(agent_name)
            task.completed_agents = json.dumps(completed)
            db.commit()
    db.close()

def update_task_result(task_id: str, result: dict):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        task.result = json.dumps(result)
        task.status = 'completed'
        db.commit()
    db.close()

def update_task_error(task_id: str, error: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        task.error = error
        task.status = 'failed'
        db.commit()
    db.close()

def cleanup_old_tasks():
    db = SessionLocal()
    cutoff = time.time() - 3600  # 1 hour
    db.query(Task).filter(Task.timestamp < cutoff).delete()
    db.commit()
    db.close()
