import os
import time
import random
from openai import OpenAI

# API Handling Configuration
# NVIDIA NIM API configuration for LLM queries.
# The API key should be set as an environment variable (NVIDIA_API_KEY) in the .env file.
# We fallback to a placeholder if not set to prevent immediate crashes, but warn the developer.
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "PLACEHOLDER_KEY_SET_NVIDIA_API_KEY_IN_ENV")
MODEL_NAME = os.getenv("MODEL_NAME", "poolside/laguna-xs-2.1")
BASE_URL = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")

class APIHandler:
    """
    Handles connections and completions from the NVIDIA NIM API.
    Utilizes exponential backoff to handle rate limits (HTTP 429) gracefully.
    """
    def __init__(self):
        # Warn if the developer has not configured their API key
        if NVIDIA_API_KEY == "PLACEHOLDER_KEY_SET_NVIDIA_API_KEY_IN_ENV":
            print("[WARNING] [API Handler] NVIDIA_API_KEY environment variable is not set. API calls will fail.")
            
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key=NVIDIA_API_KEY
        )
        print(f"[API Handler] Initialized with endpoint {BASE_URL} and model {MODEL_NAME}.")

    def generate_completion(self, prompt: str, temperature: float = 0.2, max_retries: int = 5) -> str:
        """Handles the direct API request to the LLM with robust exponential backoff."""
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=0.95,
                    max_tokens=8192,
                    stream=False
                )
                return completion.choices[0].message.content
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    sleep_time = (attempt + 1) * 3 + random.uniform(0.5, 3.0)
                    print(f"[API Handler] 429 Rate Limit. Sleeping for {sleep_time:.2f}s...", flush=True)
                    time.sleep(sleep_time)
                    continue
                if attempt == max_retries - 1:
                    return f"[API Error: {e}]"

# Export a singleton instance of the handler
api_handler = APIHandler()
