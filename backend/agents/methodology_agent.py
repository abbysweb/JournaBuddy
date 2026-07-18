import json
from tools.llm_client import call_llm_json

PROMPT = """Critique the methodology and statistical soundness of this paper.
Return a JSON object with:
- "experimental_design_score": int (0-100)
- "dataset_quality": int (0-100)
- "reproducibility": int (0-100)
- "statistics_correctness": int (0-100)
- "threats_to_validity": list of str

Paper Text:
{text}

Respond ONLY with valid JSON."""

def run(text: str) -> dict:
    prompt = PROMPT.format(text=text[:12000])
    return call_llm_json(prompt)
