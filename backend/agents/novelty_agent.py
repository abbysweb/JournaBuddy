import json
from tools.llm_client import call_llm_json

PROMPT = """Evaluate the scientific novelty of this paper.
Return a JSON object with:
- "novel_contribution_score": int (0-100)
- "research_gap_coverage": int (0-100)
- "innovation_index": int (0-100)
- "idea_similarity": int (0-100)
- "top_closest_papers": list of str (hypothetical closest papers based on topic)

Paper Text:
{text}

Respond ONLY with valid JSON."""

def run(text: str) -> dict:
    prompt = PROMPT.format(text=text[:10000])
    return call_llm_json(prompt)
