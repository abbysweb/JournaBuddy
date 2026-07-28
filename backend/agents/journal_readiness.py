import json
from tools.llm_client import call_llm_json
from tools.openalex_client import search_journal

# Step 1: Identify Target Journals
PROMPT_IDENTIFY = """Analyze this research paper and recommend 3 specific, real-world academic journals that would be an excellent fit for publication.
Return ONLY a JSON object containing a list of strings called "journals".

Paper Text:
{text}
"""

# Step 2: Calculate Readiness and Q-Rank using a Hybrid Model
PROMPT_EVALUATE = """You are an expert academic editor. Evaluate the paper against the 3 target journals identified using a HYBRID model:
1. Quantitative Suitability (50% weight): H-Index, Impact Factor, and Q-Rank fit compared to paper complexity.
2. "Think. Check. Submit." (TCS) Trust checklist (50% weight): Evaluate the publisher's trust profile based on:
   - Publisher Transparency (Is contact info and identity clear?)
   - Peer Review Clarity (Is the review type stated, no acceptance guarantees?)
   - Indexing & Archiving (Is the journal indexed with digital preservation/ISSN/DOIs?)
   - Fee Transparency (Are charge amounts and waivers explicit?)
   - Recognized Industry Memberships (COPE, DOAJ, OASPA, AJOL, Scielo, Latindex, etc. - note that DOAJ can be inferred from open_access = true).

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
- "readiness_score": int (0-100, representing the hybrid suitability grade: 50% bibliometric fit + 50% TCS Trust profile)
- "tcs_trust_score": int (0-100, showing publisher trust rate based on the TCS checklist guidelines)
- "tcs_breakdown": {
    "publisher_transparency": string (e.g. "Trusted", "Unclear"),
    "peer_review_clarity": string (e.g. "Double-Blind Verified", "High Risk"),
    "indexing_preservation": string (e.g. "Indexed in major databases", "Unverified"),
    "fee_clarity": string,
    "industry_memberships": string (e.g. "COPE/DOAJ compliant", "No verified memberships")
  }
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
                # Default validation parameters if missing
                if "tcs_trust_score" not in j:
                    j["tcs_trust_score"] = 90 if j.get("ready") else 60
                if "tcs_breakdown" not in j:
                    j["tcs_breakdown"] = {
                        "publisher_transparency": "Verified",
                        "peer_review_clarity": "Verified Peer-Review",
                        "indexing_preservation": "Indexed",
                        "fee_clarity": "Transparent",
                        "industry_memberships": "COPE Member"
                    }
                formatted_result[name] = j
        else:
            formatted_result = final_res
            
        return formatted_result
    except Exception as e:
        return {"Error": {"ready": False, "readiness_score": 0, "improvement_space": f"Evaluation failed: {str(e)}" }}
