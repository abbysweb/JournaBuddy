import json
from tools.llm_client import call_llm_json

PROMPT = """Simulate an academic peer review panel. Provide decisions from 3 independent reviewers and a final judge.
Return a JSON object with:
- "reviewer_a": "Accept" | "Minor Revision" | "Major Revision" | "Reject"
- "reviewer_b": "Accept" | "Minor Revision" | "Major Revision" | "Reject"
- "reviewer_c": "Accept" | "Minor Revision" | "Major Revision" | "Reject"
- "final_judge": "Accept" | "Minor Revision" | "Major Revision" | "Reject"
- "improvement_planner": list of {{"priority": "High"|"Medium"|"Low", "issue": str, "impact": int}}

Paper Text:
{text}

Respond ONLY with valid JSON."""

def run(text: str) -> dict:
    prompt = PROMPT.format(text=text[:12000])
    return call_llm_json(prompt)
