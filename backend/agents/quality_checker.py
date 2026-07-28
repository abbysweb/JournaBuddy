from tools.llm_client import call_llm_json
import json

PROMPT = """You are the final quality gatekeeper for academic paper review. You receive reports from four prior analysis agents.

Your job:
1. Meta-analyse ALL four reports for remaining hallucinations or bias.
2. Compute quality metrics.
3. Provide ACTIONABLE improvement suggestions — specific, concrete, with section references.

Return a JSON object with these exact keys:
- "bias_score": float 0.0 to 1.0 (0 = no bias, 1 = severe bias)
- "hallucination_detected": bool (true if you detect ANY remaining hallucination across all reports)
- "confidence": float 0.0 to 1.0 (overall confidence in the paper's quality)
- "overall_grade": str ("A", "B", "C", "D", or "F")
- "strengths": list of str (what the paper does well)
- "weaknesses": list of str (what needs improvement)
- "suggestions": list of {{"id": int, "severity": "high"|"medium"|"low", "section": str, "issue": str, "suggestion": str}}
- "verdict": str (2-3 sentence final verdict)

Proofreading report:
{proofread_report}

Citation results:
{citation_report}

Truth-checking report:
{truth_report}

Plagiarism report:
{plagiarism_report}

Original paper text (truncated):
{text}

Be BRUTALLY HONEST. No flattery. No hallucination. Only evidence-based assessment.
Respond ONLY with valid JSON."""

def run(raw_text: str, proofread_result: dict, citation_result: dict, truth_result: dict, plagiarism_result: dict) -> dict:
    """Run the quality gate agent — the final checkpoint."""
    prompt = PROMPT.format(
        text=raw_text[:10000],
        proofread_report=json.dumps(proofread_result, indent=2)[:3000],
        citation_report=json.dumps(citation_result, indent=2)[:3000],
        truth_report=json.dumps(truth_result, indent=2)[:3000],
        plagiarism_report=json.dumps(plagiarism_result, indent=2)[:3000]
    )
    result = call_llm_json(prompt)
    # Ensure required fields exist
    defaults = {
        "bias_score": 0.5,
        "hallucination_detected": False,
        "confidence": 0.5,
        "overall_grade": "C",
        "strengths": [],
        "weaknesses": [],
        "suggestions": [],
        "verdict": "Analysis could not be fully completed."
    }
    for k, v in defaults.items():
        if k not in result:
            result[k] = v
    return result
