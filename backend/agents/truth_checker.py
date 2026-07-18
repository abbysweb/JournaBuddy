from tools.llm_client import call_llm_json
import json

PROMPT = """You are a research integrity expert. You are given:
1. The original paper text
2. A proofreading report
3. Citation validation results (containing verified DOIs and titles)

Your job is to perform a Chain-of-Thought analysis to check for factual consistency:
- Identify key claims made in the paper.
- Cross-reference these claims against the validated citations provided in the citation report.
- Are there any claims that lack citation support or are contradicted by standard knowledge?
- Are there any fabricated statistics?

Return a JSON object with these exact keys:
- "hallucination_score": float 0.0 to 1.0 (0 = no hallucination, 1 = severe hallucination)
- "consistency_score": float 0.0 to 1.0 (1 = fully consistent)
- "flagged_claims": list of {{"claim": str, "issue": str, "severity": "low"|"medium"|"high"}}
- "assessment": str (brief overall assessment)

Paper text (truncated):
---
{text}
---

Proofreading report:
{proofread_report}

Citation results (Only claims supported by these titles/DOIs are strictly verified):
{citation_report}

Respond ONLY with valid JSON."""

def run(raw_text: str, proofread_result: dict, citation_result: dict) -> dict:
    """Run the truth checking agent."""
    prompt = PROMPT.format(
        text=raw_text[:12000],
        proofread_report=json.dumps(proofread_result, indent=2)[:3000],
        citation_report=json.dumps(citation_result, indent=2)[:3000]
    )
    result = call_llm_json(prompt)
    if "hallucination_score" not in result:
        result["hallucination_score"] = 0.5
        result["consistency_score"] = 0.5
    return result
