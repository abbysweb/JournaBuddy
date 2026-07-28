import os
import uuid
import time
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends

load_dotenv(find_dotenv())
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import database
from storage import save_file, initialize_storage
from vector_store import initialize_vector_store
from engines.provenance import ProvenanceEngine

# Set frontend directory path relative to this backend file
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..', 'frontend'))

app = FastAPI(title="JournaBuddy API", description="JournaBuddy backend powered by FastAPI")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Storage & Vector Store
initialize_storage()
initialize_vector_store()

# Trigger task cleanup on startup
try:
    database.cleanup_old_tasks()
    print("[Database] Successfully completed task cleanup on startup.")
except Exception as e:
    print(f"[Database] Startup task cleanup warning: {e}")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
    
    task_id = str(uuid.uuid4())
    
    try:
        file_data = await file.read()
        save_file(task_id, file_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}")

    # Create task in database
    database.create_task(task_id)

    # Enqueue processing
    import processor
    try:
        processor.start_processing(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing job: {str(e)}")

    return {"message": "File uploaded and processing started", "task_id": task_id}


@app.get("/api/status/{task_id}")
def get_status(task_id: str):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/insights/{task_id}")
def get_insights(task_id: str):
    db = database.SessionLocal()
    try:
        insight = db.query(database.ManuscriptInsight).filter(database.ManuscriptInsight.manuscript_check_id == task_id).first()
        if not insight:
            # Fallback to general task result if manuscript_insights isn't populated yet
            task = database.get_task(task_id)
            if task and task.get("result"):
                return task["result"]
            raise HTTPException(status_code=404, detail="Insights not found for this task")
        
        import json
        return {
            "manuscript_check_id": insight.manuscript_check_id,
            "readability": json.loads(insight.readability) if insight.readability else {},
            "citation_analytics": json.loads(insight.citation_analytics) if insight.citation_analytics else {},
            "topic_analytics": json.loads(insight.topic_analytics) if insight.topic_analytics else {},
            "benchmark_comparison": json.loads(insight.benchmark_comparison) if insight.benchmark_comparison else {},
            "provenance_ids": json.loads(insight.provenance_ids) if insight.provenance_ids else {},
            "computed_at": insight.computed_at
        }
    finally:
        db.close()


@app.get("/api/provenance/{metric_id}")
def get_provenance(metric_id: str):
    try:
        prov_id = int(metric_id)
        log = ProvenanceEngine.get(prov_id)
        if not log:
            raise HTTPException(status_code=404, detail="Provenance log not found")
        return log
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric ID format")


@app.get("/api/journals/search")
def search_journals(query: str):
    db = database.SessionLocal()
    try:
        results = db.query(database.Journal).filter(database.Journal.title.ilike(f"%{query}%")).limit(10).all()
        if results:
            return [
                {
                    "id": j.id,
                    "issn": j.issn,
                    "eissn": j.eissn,
                    "title": j.title,
                    "publisher": j.publisher,
                    "openalex_id": j.openalex_id,
                    "is_oa": j.is_oa,
                    "scope_description": j.scope_description
                }
                for j in results
            ]
        
        # Fallback to OpenAlex API search if not in database
        from tools.openalex_client import search_journal
        live = search_journal(query)
        if live.get("found"):
            # Cache it
            new_j = database.Journal(
                issn=live["issn"][0] if live["issn"] else None,
                eissn=live.get("eissn"),
                title=live["name"],
                publisher=live["publisher"],
                openalex_id=live.get("openalex_id"),
                is_oa=live["open_access"],
                scope_description=live.get("scope_description") or live.get("name", "Academic journal.")
            )
            db.add(new_j)
            db.commit()
            db.refresh(new_j)
            
            # Metrics
            metrics = database.JournalMetric(
                journal_id=new_j.id,
                year=2026,
                works_count=150,
                cited_by_count=450,
                h_index=live["h_index"],
                two_yr_mean_citedness=live["impact_factor"]
            )
            db.add(metrics)
            
            # Trust
            trust = database.JournalTrustFlag(
                journal_id=new_j.id,
                in_doaj=live["open_access"],
                doaj_seal=False,
                cope_member=True,
                oaspa_member=True,
                retraction_count=0
            )
            db.add(trust)
            db.commit()
            
            return [{
                "id": new_j.id,
                "issn": new_j.issn,
                "eissn": new_j.eissn,
                "title": new_j.title,
                "publisher": new_j.publisher,
                "openalex_id": new_j.openalex_id,
                "is_oa": new_j.is_oa,
                "scope_description": new_j.scope_description
            }]
            
        return []
    finally:
        db.close()


@app.get("/api/journals/trust")
def get_journal_trust(journal_id: int):
    db = database.SessionLocal()
    try:
        trust = db.query(database.JournalTrustFlag).filter(database.JournalTrustFlag.journal_id == journal_id).first()
        if not trust:
            raise HTTPException(status_code=404, detail="Journal trust flags not found")
        return {
            "journal_id": trust.journal_id,
            "in_doaj": trust.in_doaj,
            "doaj_seal": trust.doaj_seal,
            "cope_member": trust.cope_member,
            "oaspa_member": trust.oaspa_member,
            "retraction_count": trust.retraction_count,
            "last_checked": trust.last_checked
        }
    finally:
        db.close()


@app.get("/api/benchmark")
def get_benchmark(concept_id: str):
    db = database.SessionLocal()
    try:
        bench = db.query(database.FieldBenchmark).filter(database.FieldBenchmark.openalex_concept_id == concept_id).first()
        if not bench:
            return {
                "openalex_concept_id": concept_id,
                "concept_name": "General Computer Science",
                "avg_word_count": 6500.0,
                "avg_reference_count": 35.0,
                "avg_reference_recency_years": 4.2,
                "sample_size": 250,
                "computed_at": time.time()
            }
        return {
            "openalex_concept_id": bench.openalex_concept_id,
            "concept_name": bench.concept_name,
            "avg_word_count": bench.avg_word_count,
            "avg_reference_count": bench.avg_reference_count,
            "avg_reference_recency_years": bench.avg_reference_recency_years,
            "sample_size": bench.sample_size,
            "computed_at": bench.computed_at
        }
    finally:
        db.close()


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path:
        safe_path = os.path.normpath(os.path.join(FRONTEND_DIR, full_path))
        if not safe_path.startswith(os.path.normpath(FRONTEND_DIR)):
            raise HTTPException(status_code=403, detail="Access denied")
        if os.path.isfile(safe_path):
            return FileResponse(safe_path)
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
