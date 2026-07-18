import requests
import time
import json
import os

API_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Configuration loader for the API Diagnosis Tool.
# To prevent security leaks, we load configurations from a local config file if it exists,
# or dynamically from environment variables.
TEST_CONFIGS = []

CONFIG_FILE_PATH = "api_keys_config.json"

if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, "r") as config_file:
            TEST_CONFIGS = json.load(config_file)
            print(f"[Diagnosis Tool] Loaded {len(TEST_CONFIGS)} test configurations from '{CONFIG_FILE_PATH}'")
    except Exception as e:
        print(f"[Diagnosis Tool] Error reading config file {CONFIG_FILE_PATH}: {e}")

# Fallback/Append: Load from standard environment variables if defined
env_api_key = os.getenv("NVIDIA_API_KEY")
if env_api_key:
    # Check if this environment config is already loaded
    if not any(cfg.get("key") == env_api_key for cfg in TEST_CONFIGS):
        TEST_CONFIGS.append({
            "name": "NVIDIA NIM (Env Var Key)",
            "model": os.getenv("MODEL_NAME", "poolside/laguna-xs-2.1"),
            "key": env_api_key
        })

# Default local Ollama config if no other configs are found
if not TEST_CONFIGS:
    print("[Diagnosis Tool] No configuration file or env key found. Defaulting to local Ollama template.")
    TEST_CONFIGS = [
        {
            "name": "Ollama API (Local Template)",
            "model": "llama3",
            "key": os.getenv("OLLAMA_API_KEY", "default_placeholder_key"),
            "base_url": "http://localhost:11434/v1/chat/completions"
        }
    ]

def ping_api(config):
    """Pings the NVIDIA or Ollama API using the given model and API key."""
    endpoint = config.get("base_url", API_BASE_URL)
    
    headers = {
        "Authorization": f"Bearer {config['key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": "ping. reply with pong"}],
        "max_tokens": 10,
        "temperature": 0.1,
        "stream": False
    }

    start_time = time.time()
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        duration = round(time.time() - start_time, 2)
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return {
                "status": "SUCCESS",
                "code": 200,
                "duration_sec": duration,
                "reply": reply,
                "error": None
            }
        else:
            return {
                "status": "FAILED",
                "code": response.status_code,
                "duration_sec": duration,
                "reply": None,
                "error": response.text
            }
            
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return {
            "status": "ERROR",
            "code": None,
            "duration_sec": duration,
            "reply": None,
            "error": str(e)
        }

def generate_report():
    print("=" * 60)
    print(" NVIDIA API DIAGNOSIS REPORT ".center(60, "="))
    print("=" * 60)
    
    report_data = []
    success_count = 0
    fail_count = 0
    
    for i, config in enumerate(TEST_CONFIGS, 1):
        print(f"\n[{i}/{len(TEST_CONFIGS)}] Testing {config['name']} | Model: {config['model']}")
        key = config.get("key", "")
        key_prefix = f"{key[:10]}...{key[-4:]}" if len(key) >= 14 else "Placeholder/Local Key"
        print(f"Key Prefix: {key_prefix}")
        
        result = ping_api(config)
        
        # Merge result into config for the final report
        entry = {**config, **result}
        report_data.append(entry)
        
        if result["status"] == "SUCCESS":
            success_count += 1
            print(f"[SUCCESS] ({result['duration_sec']}s) - Response: {result['reply']}")
        else:
            fail_count += 1
            print(f"[FAILED] {result['status']} (Code: {result['code']}) - Error: {result['error']}")
            
    print("\n" + "=" * 60)
    print(f" SUMMARY: {success_count} SUCCESS | {fail_count} FAILED")
    print("=" * 60)
    
    # Save report to file
    report_path = "api_diagnosis_report.json"
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=4)
        
    print(f"\nDetailed JSON report saved to: {report_path}")

if __name__ == "__main__":
    generate_report()
