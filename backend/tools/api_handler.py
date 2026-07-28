import os
import time
import random
import threading
from openai import OpenAI

PLACEHOLDER_PATTERNS = ["placeholder", "your_", "changeme"]

def is_key_usable(key: str | None) -> bool:
    if not key or not key.strip():
        return False
    key_lower = key.strip().lower()
    return not any(p in key_lower for p in PLACEHOLDER_PATTERNS)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-ai/deepseek-v4-flash")
BASE_URL = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")

MAX_CONCURRENT = int(os.getenv("API_MAX_CONCURRENT", "6"))

class APIHandler:
    def __init__(self):
        self._usable = is_key_usable(NVIDIA_API_KEY)
        self._semaphore = threading.Semaphore(MAX_CONCURRENT)
        if not self._usable:
            print("[WARNING] [API Handler] NVIDIA_API_KEY is missing or looks like a placeholder. API calls will fail.")
            self.client = None
        else:
            self.client = OpenAI(base_url=BASE_URL, api_key=NVIDIA_API_KEY)
            print(f"[API Handler] Initialized with endpoint {BASE_URL} and model {MODEL_NAME}. Max concurrent: {MAX_CONCURRENT}")

    def generate_completion(self, prompt: str, temperature: float = 0.2, max_retries: int = 5) -> str:
        if not self._usable or self.client is None:
            return "[API Error: NVIDIA_API_KEY not configured]"

        self._semaphore.acquire()
        try:
            return self._call_with_retry(prompt, temperature, max_retries)
        finally:
            self._semaphore.release()

    def _call_with_retry(self, prompt: str, temperature: float, max_retries: int) -> str:
        last_error = None
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=0.95,
                    max_tokens=8192,
                    stream=False,
                    timeout=90
                )
                return completion.choices[0].message.content
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_rate_limit = "429" in str(e)
                is_timeout = "timeout" in err_str or "timed out" in err_str

                if is_rate_limit:
                    sleep_time = min(30, (2 ** attempt) + random.uniform(0.5, 2.0))
                    print(f"[API Handler] 429 Rate Limit (attempt {attempt+1}/{max_retries}). Backoff {sleep_time:.1f}s", flush=True)
                    time.sleep(sleep_time)
                elif is_timeout:
                    if attempt < max_retries - 1:
                        sleep_time = (attempt + 1) * 2
                        print(f"[API Handler] Timeout (attempt {attempt+1}/{max_retries}). Retrying in {sleep_time}s...", flush=True)
                        time.sleep(sleep_time)
                else:
                    return f"[API Error: {e}]"

        return f"[API Error: {last_error}]"

api_handler = APIHandler()
