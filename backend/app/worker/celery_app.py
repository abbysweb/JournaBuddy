import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "journabuddy",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.worker.tasks']
)

celery_app.conf.task_routes = {
    "app.worker.tasks.extract_pdf": {"queue": "io_bound"},
    "app.worker.tasks.run_agent": {"queue": "llm_bound"},
}
