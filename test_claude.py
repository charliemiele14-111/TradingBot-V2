import os
import sys
import requests

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
print(f"Anthropic key length: {len(API_KEY)} characters")

if not API_KEY:
    print("The ANTHROPIC_API_KEY secret is empty or missing.")
    sys.exit(1)

response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": "claude-haiku-5-5",
        "max_tokens": 20,
        "messages": [{"role": "user", "content": "Reply with the word: connected"}],
    },
)

print(f"Anthropic status code: {response.status_code}")
print(f"Anthropic reply: {response.text[:300]}")

if response.status_code != 200:
    print("Stopping here. Anthropic did not accept this request.")
    sys.exit(1)

print("Claude is connected and responding.")
