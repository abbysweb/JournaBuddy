import os
import json
import re
from dotenv import load_dotenv
from tools.api_handler import api_handler

# Load environment variables
load_dotenv()

USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_llm(prompt: str, temperature: float = 0.2, max_retries: int = 5) -> str:
    """Wrapper to call the LLM, trying Gemini first if configured, falling back to OpenAI, then NVIDIA NIM."""
    if USE_GEMINI and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-3.1-flash-lite")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature
                )
            )
            return response.text
        except Exception as e:
            print(f"[LLM Client] Gemini failed: {e}. Falling back.")

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM Client] OpenAI failed: {e}. Falling back.")

    # Fallback to NVIDIA NIM (via api_handler)
    return api_handler.generate_completion(prompt, temperature, max_retries)

def call_llm_json(prompt: str, temperature: float = 0.1) -> dict:
    """Call the LLM and return a parsed JSON response."""
    if USE_GEMINI and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-3.1-flash-lite")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[LLM Client] Gemini JSON mode failed: {e}. Falling back to text mode.")

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
