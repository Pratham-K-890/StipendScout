import json
import re

from openai import OpenAI

from app.config import settings
from app.exceptions import NotConfiguredError

# Picked by live-testing OpenRouter's free-model roster (which changes over
# time — don't trust this list from memory, re-check openrouter.ai/api/v1/models
# if these ever fail outright). Primary gave clean, unfenced JSON
# consistently; a sibling model in the same free pool 429'd on first try,
# confirming free-tier rate limiting is a real operational risk here — the
# auto-router is the fallback specifically to absorb that.
PRIMARY_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
FALLBACK_MODEL = "openrouter/free"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openrouter_api_key:
            raise NotConfiguredError("OPENROUTER_API_KEY is required in .env.")
        _client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)
    return _client


def _extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        bare = re.search(r"\{.*\}", text, re.DOTALL)
        if bare:
            text = bare.group(0)
    return json.loads(text)


def generate_json(prompt: str) -> dict:
    client = _get_client()
    last_error: Exception | None = None
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=60,
            )
            content = response.choices[0].message.content
            return _extract_json(content)
        except Exception as exc:  # noqa: BLE001 - deliberately broad, we fall through to the next model
            last_error = exc
            continue
    raise RuntimeError(f"All OpenRouter models failed. Last error: {last_error}")
