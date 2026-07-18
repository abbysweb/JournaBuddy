import os
import concurrent.futures
from rq import Queue
from redis import Redis
import database
import storage
import chunker
import vector_store
from tools.pdf_reader import extract_text_from_bytes
from engines import metadata_engine, semantic_engine
from agents import proofreader, citation_checker, truth_checker, quality_checker, plagiarism_checker
from agents import novelty_agent, methodology_agent, journal_readiness, ai_reviewer_panel

# Connect to Redis
redis_conn = Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)))
q = Queue('journabuddy_queue', connection=redis_conn)

def process_pipeline(task_id: str):
    """
    Main RQ worker job. It handles fetching the file, chunking, running parallel engines and agents,
    and converging the results for the massive BI dashboard.
    """
    try:
        # Step 0: Fetch from MinIO and Extract Text
        database.update_task_status(task_id, 'processing', current_agent='extraction')
        pdf_bytes = storage.get_file(f"{task_id}.pdf")
        text = extract_text_from_bytes(pdf_bytes)
        
        if text.startswith("[Error"):
            raise ValueError(text)

        # Step 0.5: Semantic Chunking and Vector Storage (v2)
        database.update_task_status(task_id, 'processing', current_agent='chunking')
        chunks = chunker.extract_and_chunk_pdf(text)
        vector_store.index_chunks(task_id, chunks)

        # Step 1: Engines
        database.update_task_status(task_id, 'processing', current_agent='engines')
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_meta = executor.submit(metadata_engine.run, text)
            future_sem = executor.submit(semantic_engine.run, text)
            meta_res = future_meta.result()
            sem_res = future_sem.result()

        # Step 2: Parallel Execution using ThreadPoolExecutor for API calls
        database.update_task_status(task_id, 'processing', current_agent='parallel_agents')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_proof = executor.submit(proofreader.run, text)
            future_cite = executor.submit(citation_checker.run, text)
            future_plag = executor.submit(plagiarism_checker.run, text)
            future_novelty = executor.submit(novelty_agent.run, text)
            future_method = executor.submit(methodology_agent.run, text)
            future_journal = executor.submit(journal_readiness.run, text)
            future_panel = executor.submit(ai_reviewer_panel.run, text)
            
            proofread_res = future_proof.result()
            database.update_task_agent_complete(task_id, 'proofreading')
            
            citation_res = future_cite.result()
            database.update_task_agent_complete(task_id, 'citation_check')
            
            plagiarism_res = future_plag.result()
            database.update_task_agent_complete(task_id, 'plagiarism_check')

            novelty_res = future_novelty.result()
            database.update_task_agent_complete(task_id, 'novelty')

            method_res = future_method.result()
            database.update_task_agent_complete(task_id, 'methodology')

            journal_res = future_journal.result()
            database.update_task_agent_complete(task_id, 'journal_readiness')

            panel_res = future_panel.result()
            database.update_task_agent_complete(task_id, 'ai_panel')
            
            # Truth checker depends on proofread & citation results
            future_truth = executor.submit(truth_checker.run, text, proofread_res, citation_res)
            truth_res = future_truth.result()
            database.update_task_agent_complete(task_id, 'truth_check')

        # Step 3: Quality Gate
        database.update_task_status(task_id, 'processing', current_agent='quality_gate')
        quality_res = quality_checker.run(text, proofread_res, citation_res, truth_res, plagiarism_res)
        database.update_task_agent_complete(task_id, 'quality_gate')

        # Final Formatting
        hallucination_pct = float(truth_res.get('hallucination_score', 0)) * 100
        bias_pct = float(quality_res.get('bias_score', 0)) * 100
        confidence_pct = float(quality_res.get('confidence', 0)) * 100
        plag_score_pct = float(plagiarism_res.get('plagiarism_score', 0)) * 100

        result = {
            "metadata": meta_res,
            "semantic": sem_res,
            "quality": {
                "grade": quality_res.get("overall_grade", "C"),
                "confidence": confidence_pct,
                "verdict": quality_res.get("verdict", "Analysis complete."),
                "structure_score": proofread_res.get("structure_score", 70),
                "strengths": quality_res.get("strengths", []),
                "weaknesses": quality_res.get("weaknesses", []),
                "suggestions": quality_res.get("suggestions", [])
            },
            "citations": {
                "coverage": citation_res.get("coverage_percent", 0.0),
                "references": [
                    {
                        "valid": ref.get("found", False),
                        "doi": ref.get("doi", ""),
                        "title": ref.get("title", "Unknown"),
                        "year": ref.get("year", "N/A")
                    }
                    for ref in citation_res.get("dois", [])
                ]
            },
            "truth_check": {
                "hallucination_score": hallucination_pct,
                "bias_score": bias_pct,
                "flagged_claims": truth_res.get("flagged_claims", [])
            },
            "plagiarism": {
                "score": plag_score_pct,
                "verdict": plagiarism_res.get("verdict", "Original"),
                "flagged": plagiarism_res.get("flagged_sentences", [])
            },
            "proofread": {
                "issues": proofread_res.get("issues", [])
            },
            "novelty": novelty_res,
            "methodology": method_res,
            "journal_readiness": journal_res,
            "ai_panel": panel_res
        }

        database.update_task_result(task_id, result)

    except Exception as e:
        database.update_task_error(task_id, str(e))

def start_processing(task_id: str):
    """Enqueues the pipeline job to RQ."""
    q.enqueue(process_pipeline, task_id)
