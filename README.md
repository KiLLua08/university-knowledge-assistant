# AI-Powered University Knowledge Assistant

## Status

🟢 **Day 3 milestone implemented:** grounded RAG answers from a local Qwen model
through LM Studio, a modular FastAPI service, centralized configuration and an
expanded mocked test suite.

This is still a learning MVP, not a production system. There is no frontend,
authentication, deployment pipeline or retrieval-quality benchmark yet.

## Overview

The assistant indexes university course PDFs into a local ChromaDB collection,
retrieves the most relevant chunks for a question, and asks a local LM Studio
model to answer **only from those chunks**. File and page references come from
retrieval metadata, so the model cannot invent citations.

## Implemented pipeline

```
PDFs in data/raw/
  -> PyMuPDF extraction (one record per page)
  -> conservative text cleaning
  -> character chunking (1000 chars, 150 overlap, per page)
  -> local Spark DataFrame filter / transform / count
  -> all-MiniLM-L6-v2 embeddings (loaded once, CPU by default)
  -> ChromaDB persistent collection at data/chroma/
  -> top-k semantic retrieval with filename + page metadata
  -> labelled context + grounding prompt
  -> qwen3.5-9b in LM Studio via OpenAI-compatible HTTP
  -> {question, answer, sources} returned by FastAPI /ask
```

See [docs/architecture.md](docs/architecture.md) for the detailed data flow and
rationale, [docs/decisions.md](docs/decisions.md) for technical choices, and
[docs/development_log.md](docs/development_log.md) for progress and actual
verification output.

## Requirements

- Windows 11, Python 3.11.9, Java 17
- PyMuPDF, PySpark 4.x, Sentence Transformers, ChromaDB, FastAPI, httpx
- LM Studio running locally with the model `qwen3.5-9b` loaded
- CPU is the default embedding device; a GPU is not required

## Setup

```powershell
# From the repository root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Optional: copy the template and adjust values locally (the .env file is ignored)
Copy-Item .env.example .env
```

Place your own PDFs in `data/raw/` (ignored by Git). A 15-page sample
`deep_learning.pdf` is used for local testing and is **not committed**.

### Configuration

All settings are read once per process from environment variables / `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_BASE_URL` | `http://localhost:1234/v1` | LM Studio OpenAI-compatible base URL |
| `LLM_MODEL` | `qwen3.5-9b` | Model ID requested from LM Studio |
| `LLM_API_KEY` | `lm-studio` | Local API key sent as a Bearer token |
| `LLM_TEMPERATURE` | `0.2` | Low randomness for grounded answers |
| `LLM_MAX_TOKENS` | `2048` | Enough room for Qwen's reasoning plus the final answer |
| `LLM_TIMEOUT_SECONDS` | `120` | HTTP request timeout |
| `RETRIEVAL_TOP_K` | `3` | Default number of chunks retrieved |
| `CHROMA_PERSIST_DIRECTORY` | `data/chroma` | Local vector store path |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Must match indexing |
| `EMBEDDING_DEVICE` | `cpu` | Embedding device |

Secrets are never logged. Do not commit `.env`, PDFs, ChromaDB data, model files
or `.venv`.

## Usage

```powershell
# Run all automated tests (offline; no LM Studio or model download needed)
python -m pytest -v

# Extract, clean, chunk, process with Spark, embed and index every PDF
python scripts/index_documents.py

# Retrieve the top 3 chunks for a sample question
python scripts/test_retrieval.py

# Ask the full RAG pipeline (requires LM Studio)
python scripts/test_rag.py --question "What is backpropagation?" --top-k 3

# Start the API
python -m uvicorn university_knowledge_assistant.api.main:app --reload
```

API endpoints:

- `GET /health` — liveness only; it reports `llm_status: "not_checked"` and does
  not falsely claim that LM Studio was probed.
- `POST /ask` — body `{"question": "...", "top_k": 3}`; `top_k` is optional.
- `GET /docs` — interactive Swagger UI.

Example:

```powershell
curl -X POST http://127.0.0.1:8000/ask `
  -H "Content-Type: application/json" `
  -d '{"question":"What is backpropagation?","top_k":3}'
```

When no chunks are retrieved, `/ask` returns a clear "no supporting course
material" answer and an empty `sources` list; the LLM is not called.

The first indexing run downloads the ~90 MB MiniLM model from Hugging Face.
Later runs reuse the local cache. Qwen is hosted by LM Studio and is never
downloaded or fine-tuned by this project.

### Qwen reasoning models

`qwen3.5-9b` returns a separate `reasoning_content` field. With a small
`LLM_MAX_TOKENS` budget the visible `content` can be empty; the default `2048`
leaves room for the final answer. If LM Studio returns only reasoning, the
service raises a clear `LLMResponseError` rather than presenting hidden
reasoning as the answer.

## Repository structure

```
src/university_knowledge_assistant/
├── api/            # FastAPI app, routes, dependencies, Pydantic schemas
├── config.py       # centralized validated settings
├── data/           # PDF extraction (pdf_loader.py)
├── preprocessing/  # text_cleaner.py, chunker.py
├── pipelines/      # local PySpark pipeline + RAG pipeline
├── models/         # Sentence Transformers embedding wrapper
├── retrieval/      # ChromaDB vector store
├── services/       # LM Studio HTTP client
└── utils/          # shared Spark environment helper
scripts/
├── index_documents.py          # end-to-end indexing
├── test_retrieval.py           # manual retrieval check
├── test_rag.py                 # manual full RAG check
└── spark_smoke_test.py         # Day 1 environment check
tests/                          # pytest suite
docs/                           # architecture, log and decisions
data/raw/                       # local PDFs (Git-ignored)
data/chroma/                    # ChromaDB persistence (Git-ignored)
```

## Test results

`python -m pytest -v` → **84 passed**.

The suite mocks the LLM HTTP client, embedding model and retrieval layer, so it
needs neither LM Studio nor a model download. It also uses FastAPI `TestClient`
for `/health`, `/ask`, validation errors, 502 LLM failures and `/docs`.

Real local verification with LM Studio:

- `qwen3.5-9b` was listed by `GET /v1/models` with HTTP 200.
- `scripts/test_rag.py` returned a grounded backpropagation answer with 3
  sources from `deep_learning.pdf` pages 4 and 5.
- A live uvicorn server returned `/health` 200, `/docs` 200 and `/ask` 200 with
  a 962-character answer and 3 metadata-derived sources.

Full commands and output are recorded in
[docs/development_log.md](docs/development_log.md).

## Planned (not implemented)

- Retrieval relevance benchmark and evaluation metrics
- Minimal frontend / chat UI
- OCR for scanned PDFs and hybrid keyword + semantic search
- PostgreSQL metadata storage and larger-scale distributed processing
- Authentication, Docker/Kubernetes and cloud deployment claims

## Academic objectives

This project is a practical way to study Deep Learning, NLP, Transformers,
Information Retrieval, Big Data processing, data engineering, software testing
and system architecture.

## Documentation

- [Project Scope](docs/project_scope.md)
- [Architecture](docs/architecture.md)
- [Development Log](docs/development_log.md)
- [Decisions](docs/decisions.md)
- [Tests](tests/README.md)

## Data and licensing

Do not commit university PDFs or other copyrighted course material: `data/raw/`
and `data/chroma/` are Git-ignored. The repository's own license is to be
determined.
