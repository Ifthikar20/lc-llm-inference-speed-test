import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import prompts
from .chunk import chunk_text
from .config import settings
from .ollama_client import OllamaError, generate
from .pdf import extract_text

app = FastAPI(title="Local LLM Q&A POC", version="0.2.0")

STATIC_DIR = Path(__file__).parent / "static"


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
    return await _extract(req.material, req.num_questions, req.model)


@app.post("/extract-from-pdf")
async def extract_from_pdf(
    file: UploadFile = File(...),
    num_questions: int = Form(5),
    model: str | None = Form(None),
) -> dict:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file.")
    data = await file.read()
    try:
        material = extract_text(data)
    except Exception as exc:  # pypdf raises a variety of parse errors
        raise HTTPException(400, f"Could not read PDF: {exc}") from exc
    if not material:
        raise HTTPException(400, "No extractable text found in the PDF.")
    num_questions = max(1, min(num_questions, 20))
    result = await _extract(material, num_questions, model)
    result["chars_extracted"] = len(material)
    return result


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
        "stats": _stats(result),
    }


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


async def _extract(material: str, num_questions: int, model: str | None) -> dict:
    chunks = chunk_text(material)
    if not chunks:
        raise HTTPException(400, "Material is empty after processing.")

    per_chunk = max(1, num_questions // len(chunks))
    questions: list[dict] = []
    stats: list[dict] = []
    for chunk in chunks:
        prompt = prompts.EXTRACT_QUESTIONS.format(n=per_chunk, material=chunk)
        try:
            result = await generate(prompt, model=model)
        except OllamaError as exc:
            raise HTTPException(502, str(exc)) from exc
        stats.append(_stats(result))
        questions.extend(_parse_questions(result["text"]))
        if len(questions) >= num_questions:
            break

    return {"questions": questions[:num_questions], "stats": stats}


def _stats(result: dict) -> dict:
    return {k: result[k] for k in ("elapsed_sec", "eval_count", "tokens_per_sec")}


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
