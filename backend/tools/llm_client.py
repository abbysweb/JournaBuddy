import json
import re
from tools.api_handler import api_handler, NVIDIA_API_KEY, is_key_usable

def parse_json_safely(raw: str):
    try:
        cleaned = raw.strip()
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL | re.IGNORECASE)
        if json_match:
            cleaned = json_match.group(1).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    try:
        cleaned = raw.strip()
        start_idx = cleaned.find('[')
        end_idx = cleaned.rfind(']')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return json.loads(cleaned[start_idx:end_idx+1])
    except json.JSONDecodeError:
        pass

    try:
        cleaned = raw.strip()
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return json.loads(cleaned[start_idx:end_idx+1])
    except json.JSONDecodeError:
        pass

    print(f"[LLM Client] JSON Parse Error. Raw: {raw[:200]}...")
    return {"raw_response": raw, "parse_error": True, "error_msg": "Failed to parse JSON"}

def call_llm(prompt: str, temperature: float = 0.2, max_retries: int = 2) -> str:
    if not is_key_usable(NVIDIA_API_KEY):
        raise Exception("NVIDIA_API_KEY not configured or is a placeholder. Set NVIDIA_API_KEY in .env")
    res = api_handler.generate_completion(prompt, temperature, max_retries)
    if res and not res.startswith("[API Error:"):
        return res
    raise Exception(f"LLM call failed: {res}")

def call_llm_json(prompt: str, temperature: float = 0.1):
    raw = call_llm(prompt, temperature)
    return parse_json_safely(raw)
