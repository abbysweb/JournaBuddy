from tools.llm_client import call_llm_json

prompt = """
You are a methodology expert. Please analyze this mock text and return a JSON object with:
{"score": 95, "verdict": "Excellent"}

MOCK TEXT: The study used a double-blind randomized control trial.
"""

print("Sending request to poolside/laguna-xs-2.1...")
result = call_llm_json(prompt)
print("\n--- Parsed JSON Result ---")
print(result)
