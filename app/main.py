import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import prompts
from .chunk import chunk_text
from .config import settings
from .ollama_client import OllamaError, generate

app = FastAPI(title="Local LLM Q&A POC", version="0.1.0")


class ExtractRequest(BaseModel):
    material: str = Field(..., min_length=1)
    num_questions: int = Field(5, ge=1, le=20)
    model: str | None = None


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1)
    context: str = Field(..., min_length=1)
    model: str | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": settings.model}


@app.post("/extract-questions")
async def extract_questions(req: ExtractRequest) -> dict:
    chunks = chunk_text(req.material)
    if not chunks:
        raise HTTPException(400, "Material is empty after processing.")

    # Spread the requested question count across chunks so large docs are covered.
    per_chunk = max(1, req.num_questions // len(chunks))
    questions: list[dict] = []
    stats: list[dict] = []
    for chunk in chunks:
        prompt = prompts.EXTRACT_QUESTIONS.format(n=per_chunk, material=chunk)
        try:
            result = await generate(prompt, model=req.model)
        except OllamaError as exc:
            raise HTTPException(502, str(exc)) from exc
        stats.append(
            {k: result[k] for k in ("elapsed_sec", "eval_count", "tokens_per_sec")}
        )
        questions.extend(_parse_questions(result["text"]))
        if len(questions) >= req.num_questions:
            break

    return {"questions": questions[: req.num_questions], "stats": stats}


@app.post("/answer")
async def answer(req: AnswerRequest) -> dict:
    prompt = prompts.ANSWER_WITH_CONTEXT.format(
        context=req.context, question=req.question
    )
    try:
        result = await generate(prompt, model=req.model)
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {
        "answer": result["text"].strip(),
        "stats": {
            "elapsed_sec": result["elapsed_sec"],
            "eval_count": result["eval_count"],
            "tokens_per_sec": result["tokens_per_sec"],
        },
    }


def _parse_questions(text: str) -> list[dict]:
    """Reasoning models often wrap JSON in <think> blocks or fences; pull out
    the first JSON object and read its `questions` array."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return data.get("questions", []) if isinstance(data, dict) else []
