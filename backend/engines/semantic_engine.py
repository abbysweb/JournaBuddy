import json
from tools.llm_client import call_llm_json

PROMPT = """Analyze the semantic quality and readability of this text.
Return a JSON object with:
- "readability_score": int (0-100)
- "academic_tone": int (0-100)
- "passive_voice_percent": int
- "vocabulary_richness": int (0-100)
- "section_scores": list of {{"section": str, "score": int}} (e.g. Abstract, Introduction, Methodology, Results, Conclusion)

Paper Text:
{text}

Respond ONLY with valid JSON."""

def run(text: str) -> dict:
    prompt = PROMPT.format(text=text[:10000])
    return call_llm_json(prompt)
