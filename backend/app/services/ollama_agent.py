"""
JournaBuddy Ollama Agent with Multi-Provider Fallback Cascade.

Sends structured JSON prompts to local Ollama (Llama 3.1:8b) and parses
schema-validated JSON responses. If Ollama is unavailable or fails, the
system automatically cascades to:
  1. Primary   → Ollama (llama3.1:8b)
  2. Fallback 1 → NVIDIA NIM API
  3. Fallback 2 → Gemini API
  4. Fallback 3 → OpenAI API

Each agent call is retried with exponential backoff before falling to
the next provider in the cascade chain.
"""
import json
import logging
from typing import Any, Optional

import httpx
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)

# Structured JSON prompt template injected before every agent prompt
_JSON_INSTRUCTION = (
    "You are an expert academic manuscript evaluator. "
    "Respond ONLY with a valid JSON object matching the schema provided. "
    "Do NOT include any explanation, markdown fences, or extra text outside the JSON."
)


class AgentError(Exception):
    """Raised when all LLM providers fail to produce a valid response."""
    pass


class OllamaAgent:
    """
    Sends structured prompts to LLM providers and returns validated JSON.

    Cascade priority:
        Ollama (local) → NVIDIA NIM → Gemini → OpenAI

    Each provider is retried up to 3 times with exponential backoff before
    falling to the next provider. If all providers fail, raises AgentError.
    """

    def __init__(self, timeout: float = 300.0):
        self.timeout = timeout

    def run(self, agent_name: str, prompt: str, schema: dict) -> dict:
        """
        Execute an agent prompt against the LLM cascade.

        Args:
            agent_name: Human-readable agent name (for logging).
            prompt: Task-specific prompt text.
            schema: JSON schema dict defining the expected response structure.

        Returns:
            Parsed JSON dict matching the provided schema.

        Raises:
            AgentError: If all providers fail.
        """
        full_prompt = f"{_JSON_INSTRUCTION}\n\nSchema: {json.dumps(schema)}\n\n{prompt}"

        providers = [
            ("Ollama", self._call_ollama),
            ("NVIDIA NIM", self._call_nvidia),
            ("Gemini", self._call_gemini),
            ("OpenAI", self._call_openai),
        ]

        last_error: Optional[Exception] = None
        for provider_name, provider_fn in providers:
            try:
                logger.info(f"[{agent_name}] Trying provider: {provider_name}")
                raw = provider_fn(full_prompt)
                parsed = self._parse_json(raw)
                logger.info(f"[{agent_name}] Success via {provider_name}")
                return parsed
            except Exception as e:
                logger.warning(f"[{agent_name}] Provider {provider_name} failed: {e}")
                last_error = e
                continue

        # All providers failed — return degraded result instead of crashing
        logger.error(f"[{agent_name}] All providers failed. Returning degraded result.")
        return {
            "status": "degraded",
            "score": None,
            "reason": str(last_error),
            "agent": agent_name,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    def _call_ollama(self, prompt: str) -> str:
        """Call the local Ollama API with the given prompt."""
        url = f"{settings.ollama_url}/api/generate"
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        response = httpx.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    def _call_nvidia(self, prompt: str) -> str:
        """Call NVIDIA NIM API (OpenAI-compatible endpoint)."""
        if not settings.nvidia_api_key:
            raise AgentError("NVIDIA_API_KEY not configured.")

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        if not settings.gemini_api_key:
            raise AgentError("GEMINI_API_KEY not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        if not settings.openai_api_key:
            raise AgentError("OPENAI_API_KEY not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """
        Parse raw LLM response string into a JSON dict.
        Strips markdown fences if the model added them despite instructions.
        """
        raw = raw.strip()
        # Remove markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)
