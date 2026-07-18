import json
import re
from tools.api_handler import api_handler

def call_llm(prompt: str, temperature: float = 0.2, max_retries: int = 5) -> str:
    """Wrapper to call the LLM using the separated API handler."""
    return api_handler.generate_completion(prompt, temperature, max_retries)

def call_llm_json(prompt: str, temperature: float = 0.1) -> dict:
    """Call the LLM and return a parsed JSON response."""
    raw = call_llm(prompt, temperature)
    try:
        cleaned = raw.strip()
        
        # Robust extraction: find markdown blocks first
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL | re.IGNORECASE)
        if json_match:
            cleaned = json_match.group(1).strip()
        else:
            # Fallback: extract substring between first { and last }
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx+1]
        
        return json.loads(cleaned)
    except Exception as e:
        print(f"[LLM Client] JSON Parse Error: {e}. Raw response: {raw[:200]}...")
        # Return raw response along with parse error details for recovery
        return {
            "raw_response": raw,
            "parse_error": True,
            "error_msg": str(e)
        }
