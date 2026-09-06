import json
import os

import requests

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
DEFAULT_MODEL = "mistral-small-latest"


def call(messages, model, system_prompt):
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY is not set.")
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected Mistral response: {json.dumps(data)[:400]}")
