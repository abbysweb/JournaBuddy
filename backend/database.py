import os
import json
import time
from sqlalchemy import create_engine, Column, String, Float, Text
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

# We will use Alembic for migrations, but we can call create_all for local dev fallback
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
