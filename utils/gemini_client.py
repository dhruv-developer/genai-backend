import json
import logging
from typing import Optional, Dict, Any
import requests
from settings import settings

logger = logging.getLogger("gemini_client")
logger.setLevel(logging.INFO)

GEMINI_ENDPOINT = f"{settings.GEMINI_URL}/{settings.GEMINI_MODEL}:generateContent"
API_KEY_HEADER = {"X-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"}


def call_gemini(prompt: str, max_output_tokens: int = 512, temperature: float = 0.2) -> Dict[str, Any]:
    """
    Calls Gemini generateContent and returns parsed JSON. The prompt *should* instruct Gemini to return JSON
    if you expect structured output. This function does basic parsing but is defensive.
    """
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
    }

    try:
        resp = requests.post(GEMINI_ENDPOINT, headers=API_KEY_HEADER, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.exception("Gemini request failed")
        raise RuntimeError(f"Gemini API request failed: {e}")

    # The API's response structure can vary. Try to extract candidate text(s).
    # Typical shape: {'candidates':[{'output':'...'}], ...} or nested choices.
    text_out = ""
    try:
        # Try a few common shapes
        if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
            text_out = data["candidates"][0].get("output", "") or data["candidates"][0].get("content", "")
        elif "output" in data and isinstance(data["output"], dict):
            # maybe output->content->parts
            out = data["output"]
            if "content" in out and isinstance(out["content"], list):
                # join parts text
                parts = []
                for item in out["content"]:
                    for part in item.get("parts", []):
                        parts.append(part.get("text", ""))
                text_out = "\n".join(parts)
            else:
                text_out = str(out)
        else:
            # fallback: raw text anywhere
            text_out = json.dumps(data)
    except Exception:
        text_out = json.dumps(data)

    # Try to parse as JSON if model was asked to output JSON
    try:
        parsed = json.loads(text_out)
        return {"raw": data, "text": text_out, "json": parsed}
    except Exception:
        return {"raw": data, "text": text_out, "json": None}
