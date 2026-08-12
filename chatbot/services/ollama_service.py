import requests
from django.conf import settings

# OLLAMA_URL = getattr(settings, "OLLAMA_URL", "http://localhost:11434")
OLLAMA_URL = getattr(settings, "OLLAMA_URL", "https://api.ollama.com")
MODEL_NAME = getattr(settings, "OLLAMA_MODEL", "qwen3-coder:480b-cloud")

OLLAMA_API_KEY = getattr(settings, "OLLAMA_API_KEY", None)

def chat(messages, tools=None):
    if not OLLAMA_API_KEY:
        raise RuntimeError("OLLAMA_API_KEY is not set. Check your .env file.")

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    return response.json()