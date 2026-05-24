# Local LLM Q&A POC

A minimal FastAPI service that wraps a locally-hosted LLM (via [Ollama](https://ollama.com))
to **extract exam-style questions** from study material and **answer questions**
against supplied context. Built to test local inference speed vs. hosted APIs.

## Architecture

```
material ──▶ chunk ──▶ FastAPI ──▶ Ollama (localhost:11434) ──▶ model
                          │
                          ├─ POST /extract-questions  (material -> MCQs as JSON)
                          └─ POST /answer             (question + context -> answer)
```

Every response includes timing/throughput `stats` (`elapsed_sec`, `eval_count`,
`tokens_per_sec`) so you can measure real local inference speed.

## Setup

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

