import json
import time
from collections.abc import AsyncIterator

import httpx

from .config import settings


class OllamaError(RuntimeError):
    pass


async def generate_stream(
    prompt: str, *, model: str | None = None
) -> AsyncIterator[str]:
    """Stream text deltas from Ollama's /api/generate as they're produced."""
    payload = {
        "model": model or settings.model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": settings.keep_alive,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            async with client.stream(
                "POST", f"{settings.ollama_base_url}/api/generate", json=payload
            ) as resp:
                if resp.status_code != 200:
                    await resp.aread()
                    raise OllamaError(f"Ollama returned {resp.status_code}: {resp.text}")
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line).get("response", "")
                    if chunk:
                        yield chunk
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc


async def generate(prompt: str, *, model: str | None = None) -> dict:
    """Call Ollama's /api/generate and return the text plus timing/token stats."""
    payload = {
        "model": model or settings.model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": settings.keep_alive,
    }
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate", json=payload
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    data = resp.json()
    elapsed = time.perf_counter() - started
    eval_count = data.get("eval_count", 0)
    eval_ns = data.get("eval_duration", 0) or 0
    tokens_per_sec = (eval_count / (eval_ns / 1e9)) if eval_ns else None

    return {
        "text": data.get("response", ""),
        "model": data.get("model"),
        "elapsed_sec": round(elapsed, 3),
        "eval_count": eval_count,
        "tokens_per_sec": round(tokens_per_sec, 2) if tokens_per_sec else None,
    }
