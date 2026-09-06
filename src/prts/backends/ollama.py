import json
import os

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "llama3"


def call(messages, model, system_prompt):
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected Ollama response: {json.dumps(data)[:400]}")
