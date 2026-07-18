from tools.llm_client import call_llm_json

PROMPT_TEMPLATE = """You are an expert academic writing proofreader and editor. Your job is to check this draft research paper for software quality, readability, grammar issues, nominalizations, passive voice overuse, and academic tone.

Draft text (truncated for analysis):
---
{text}
---

Provide feedback in JSON format with these exact keys:
1. "issues": A list of dicts, each with keys "type" (e.g. "grammar", "clarity", "tone"), "original" (the problematic sentence), and "suggestion" (how to improve it).
2. "structure_assessment": A text string assessing the overall structural readability of the sections (abstract, intro, methods, evaluation, conclusion).
3. "structure_score": An integer from 0 to 100 representing writing quality.
4. "summary": A brief summary of the paper.

Respond ONLY with valid JSON."""

def run(raw_text: str) -> dict:
    """Run the Proofreader Agent."""
    # Truncate text to avoid token limits (around 15000 characters)
    sample_text = raw_text[:15000]
    result = call_llm_json(PROMPT_TEMPLATE.format(text=sample_text))
    
    # Guarantee consistent fields
    if "issues" not in result or not isinstance(result["issues"], list):
        result["issues"] = []
    if "structure_assessment" not in result:
        result["structure_assessment"] = "Structure could not be parsed."
    if "structure_score" not in result:
        result["structure_score"] = 70
    if "summary" not in result:
        result["summary"] = "No summary available."
        
    return result
