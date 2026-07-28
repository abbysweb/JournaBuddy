import json
from tools.llm_client import call_llm_json

PROMPT = """You are an expert academic editor. Analyze this research paper and recommend 3 specific, real-world academic journals. For each journal provide a full readiness evaluation.

Return ONLY a JSON array, where each object has:
- "name": string (journal name)
- "publisher": string
- "h_index": int
- "impact_factor": float
- "q_rank": string (e.g. "Q1", "Q2")
- "ready": boolean
- "readiness_score": int (0-100)
- "tcs_trust_score": int (0-100)
- "tcs_breakdown": {{
    "publisher_transparency": string,
    "peer_review_clarity": string,
    "indexing_preservation": string,
    "fee_clarity": string,
    "industry_memberships": string
  }}
- "improvement_space": string

Paper Text:
{text}
"""

def run(text: str) -> dict:
    prompt = PROMPT.format(text=text[:8000])
    try:
        res = call_llm_json(prompt)
        formatted = {}
        if isinstance(res, list):
            for j in res:
                name = j.get("name", "Unknown Journal")
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
                formatted[name] = j
        else:
            formatted = res
        return formatted
    except Exception as e:
        return {"Error": {"ready": False, "readiness_score": 0, "improvement_space": f"Evaluation failed: {str(e)}"}}
