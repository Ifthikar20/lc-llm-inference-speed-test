# Local LLM Q&A POC

A minimal FastAPI service + web UI that wraps a locally-hosted LLM (via
[Ollama](https://ollama.com)) to **extract exam-style questions** from study
material (including **uploaded PDFs**) and **answer questions** against supplied
context. Built to test local inference speed vs. hosted APIs.

## Architecture

```
PDF upload ─▶ extract text ─▶ chunk ─▶ FastAPI ─▶ Ollama (localhost:11434) ─▶ model
   (UI)                                   │              │
                                          │        JSON response
                                          │              ▼
                                          │      parsed into MCQs ─▶ rendered in UI
                                          ├─ POST /extract-from-pdf  (PDF -> MCQs)
                                          ├─ POST /extract-questions (text -> MCQs)
                                          └─ POST /answer            (question+context)
```

Open http://localhost:8000/ for the upload UI: pick a PDF, choose how many
questions, hit Generate, and answer the interactive multiple-choice cards.

Every response includes timing/throughput `stats` (`elapsed_sec`, `eval_count`,
`tokens_per_sec`) so you can measure real local inference speed.

## Quick start (one command)

```bash
./run.sh
```
This checks Ollama is installed, starts its server, pulls the model if missing,
sets up the Python venv, installs deps, and launches the app at
http://localhost:8000/. Override defaults with env vars:
```bash
LLM_MODEL=qwen2.5:14b PORT=9000 ./run.sh
```
The only prerequisite is [installing Ollama](https://ollama.com/download).

## Manual setup

1. Install and start Ollama, then pull a model:
   ```bash
   ollama pull deepseek-r1:14b      # strong reasoning, ~8-10GB at Q4
   # alternatives: qwen2.5:14b, llama3.1:8b
   ```
2. Create a virtualenv and install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
   Open http://localhost:8000/docs for the interactive UI.

## Configuration

Override defaults with env vars (prefix `LLM_`):

| Variable           | Default                  | Purpose                |
|--------------------|--------------------------|------------------------|
| `LLM_MODEL`        | `deepseek-r1:14b`        | Ollama model tag       |
| `LLM_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint     |
| `LLM_REQUEST_TIMEOUT` | `300`                 | Per-request timeout (s)|

## Endpoints

**`POST /extract-from-pdf`** (multipart) — `file` (PDF), `num_questions`, optional `model`.

**`POST /extract-questions`**
```json
{ "material": "AWS S3 offers 11 nines of durability...", "num_questions": 5 }
```

**`POST /answer`**
```json
{ "question": "What is S3 durability?", "context": "S3 offers 11 nines..." }
```

## Speed test

```bash
python bench.py deepseek-r1:14b 3
```
Runs the model N times and reports median tokens/sec.
```

