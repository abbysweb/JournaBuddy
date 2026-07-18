import json
from tools.llm_client import call_llm_json

PROMPT = """Extract the core metadata from this research paper.
Return a JSON object with:
- "title": str
- "authors": list of str
- "institutions": list of str
- "abstract": str
- "keywords": list of str

Paper Text:
{text}

Respond ONLY with valid JSON."""

def run(text: str) -> dict:
    prompt = PROMPT.format(text=text[:8000])
    return call_llm_json(prompt)
