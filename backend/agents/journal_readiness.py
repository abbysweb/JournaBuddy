import json
from tools.llm_client import call_llm_json
from tools.openalex_client import search_journal

# Step 1: Identify Target Journals
PROMPT_IDENTIFY = """Analyze this research paper and recommend 3 specific, real-world academic journals that would be an excellent fit for publication.
Return ONLY a JSON object containing a list of strings called "journals".

Paper Text:
{text}
"""

# Step 2: Calculate Readiness and Q-Rank
PROMPT_EVALUATE = """You are an expert academic editor. Evaluate the paper against the 3 target journals identified.
We have fetched real bibliometric data for these journals. Using the H-Index and Impact Factor provided, deduce their official SCImago Ranking (Q1, Q2, Q3, or Q4) where Q1 is the top 25%.
Then, for each journal, provide concrete spaces for improvement specific to that journal's prestige.

Real Journal Data:
{journal_data}

Paper Text:
{text}

Return ONLY a JSON array, where each object has:
- "name": string (the journal name)
- "publisher": string
- "h_index": int
- "impact_factor": float
- "q_rank": string (e.g. "Q1", "Q2")
- "ready": boolean
- "readiness_score": int (0-100)
- "improvement_space": string (Concrete, real actionable feedback for this specific journal)
"""

def run(text: str) -> dict:
    sample_text = text[:8000]
    
    # 1. Identify Journals
    identification_prompt = PROMPT_IDENTIFY.format(text=sample_text)
    try:
        id_res = call_llm_json(identification_prompt)
        target_journals = id_res.get("journals", ["IEEE Access", "Nature", "PLOS One"])[:3]
    except Exception:
        target_journals = ["IEEE Access", "Nature", "PLOS One"]
        
    # 2. Fetch Live Metrics
    live_metrics = []
    for journal in target_journals:
        metrics = search_journal(journal)
        live_metrics.append(metrics)
        
    metrics_str = json.dumps(live_metrics, indent=2)
    
    # 3. Evaluate Readiness & Q-Rank
    eval_prompt = PROMPT_EVALUATE.format(journal_data=metrics_str, text=sample_text)
    try:
        final_res = call_llm_json(eval_prompt)
        
        # Format the output into a dictionary keyed by journal name for the frontend
        formatted_result = {}
        if isinstance(final_res, list):
            for j in final_res:
                name = j.get("name", "Unknown Journal")
                formatted_result[name] = j
        else:
            formatted_result = final_res
            
        return formatted_result
    except Exception as e:
        return {"Error": {"ready": False, "readiness_score": 0, "improvement_space": f"Evaluation failed: {str(e)}" }}
