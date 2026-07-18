"""
API Verification Script
Author: Abdullah Al Mamun (ORCID: 0009-0006-7473-0024)
Institution: TU Wien (Vienna, Austria) & Daffodil International University
Contact: mamun.swe.de@gmail.com
"""

import requests
import os

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Diffusion test
def test_diffusion():
    print("Testing Diffusion...")
    url = f"{NVIDIA_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('NVIDIA_API_KEY', 'YOUR_API_KEY_HERE')}",
        "Accept": "application/json",
    }
    payload = {
        "messages": [{"role": "user", "content": "A cute puppy"}],
        "model": "google/diffusiongemma-26b-a4b-it",
        "chat_template_kwargs": {"enable_thinking": True},
        "max_tokens": 100
    }
    r = requests.post(url, headers=headers, json=payload)
    print("Diffusion status:", r.status_code)
    if r.status_code == 200:
        print(r.json())
    else:
        print(r.text)

# TTS test
def test_tts():
    print("Testing TTS...")
    # Typically TTS is /audio/speech or something, but the user snippet didn't provide endpoint URL for TTS!
    # Wait, the user snippet for TTS just said: https://build.nvidia.com/resembleai/chatterbox-multilingual-tts/deploy
    # I don't know the exact endpoint for NIM TTS. Usually it's /audio/speech or /audio/generation
    pass

if __name__ == "__main__":
    test_diffusion()
