import requests


def call_local_judge(prompt: str, model_name: str = "opencoder:8b") -> str:
    """Sends evaluation prompt directly to local Ollama instance."""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0},  # Force deterministic scoring for testing
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Local judge connection failed: {e}")
