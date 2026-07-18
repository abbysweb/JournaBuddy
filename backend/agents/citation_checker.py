from tools.crossref_client import validate_citations
from tools.llm_client import call_llm_json

PROMPT_TEMPLATE = """You are a citation extraction assistant.
Given the following academic paper text, find the "References" or "Bibliography" section, and extract a list of the paper titles that are cited.
If you cannot find a dedicated references section, do your best to extract titles of any papers mentioned in the text.
Return ONLY a JSON object with a single key "citations", mapping to a list of strings (the titles).

Draft text (truncated for analysis):
---
{text}
---

Respond ONLY with valid JSON."""

def run(raw_text: str) -> dict:
    """Run the citation checking agent."""
    sample_text = raw_text[-15000:] # Focus on the end of the paper for references
    
    try:
        extraction = call_llm_json(PROMPT_TEMPLATE.format(text=sample_text))
        citations = extraction.get("citations", [])
    except Exception:
        citations = []
        
    result = validate_citations(citations)
    return result
