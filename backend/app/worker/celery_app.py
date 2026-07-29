"""
JournaBuddy Celery Application Configuration
Sets up the Celery distributed task queue with Redis as the broker and result backend.
Configures two named queues:
  - io_bound: PDF extraction, chunking, embedding, MinIO operations
  - llm_bound: LLM agent runs (Ollama / NVIDIA NIM / Gemini / OpenAI)
"""
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "journabuddy",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Suppress Celery 6.0 startup deprecation warning
    broker_connection_retry_on_startup=True,

    # Results expire after 24 hours
    result_expires=86400,

    # Route tasks to correct queues
    task_routes={
        "app.worker.tasks.extract_pdf_task": {"queue": "io_bound"},
        "app.worker.tasks.run_agent_task": {"queue": "llm_bound"},
    },

    # Soft time limit: 10 min per task, hard kill at 12 min
    task_soft_time_limit=600,
    task_time_limit=720,
)
