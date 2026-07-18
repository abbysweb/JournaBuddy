import os
import json
import logging
from pydantic import BaseModel
from tools.llm_client import USE_GEMINI, GEMINI_API_KEY, OPENAI_API_KEY

def call_llm_router(prompt: str, schema: BaseModel, temperature: float = 0.3) -> dict:
    """
    Routes the request to the best available LLM, enforcing the Pydantic schema.
    Tries Gemini first, falls back to OpenAI, then Ollama.
    """
    # Create system instructions explaining the expected JSON format based on the schema
    schema_json = schema.model_json_schema()
    system_prompt = f"You are a strict data extraction AI. You MUST output ONLY valid JSON exactly matching this schema:\n{json.dumps(schema_json, indent=2)}\n\nDo not include markdown blocks like ```json."
    
    full_prompt = f"{system_prompt}\n\nUSER PROMPT:\n{prompt}"
    
    # 1. Try Gemini
    if USE_GEMINI and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            # Validate with pydantic
            validated = schema(**data)
            return validated.model_dump()
        except Exception as e:
            logging.error(f"Gemini failed: {e}. Falling back to OpenAI.")
            
    # 2. Try OpenAI
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            validated = schema(**data)
            return validated.model_dump()
        except Exception as e:
            logging.error(f"OpenAI failed: {e}. Falling back to Ollama.")

    # 3. Try Local Ollama
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    try:
        import requests
        payload = {
            "model": "llama3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature}
        }
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        r.raise_for_status()
        data = json.loads(r.json()["message"]["content"])
        validated = schema(**data)
        return validated.model_dump()
    except Exception as e:
        logging.error(f"Ollama failed: {e}.")
        raise Exception("All LLM routers failed to generate valid structured JSON.")
