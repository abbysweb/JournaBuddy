from app.worker.celery_app import celery_app

@celery_app.task(bind=True)
def extract_pdf(self, file_path):
    pass

@celery_app.task(bind=True)
def run_agent(self, agent_name, payload):
    pass
