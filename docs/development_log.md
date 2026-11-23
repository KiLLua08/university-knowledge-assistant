# Development Log

This document tracks the development milestones and progress of the AI-Powered
University Knowledge Assistant project.

---

## Milestone 2 — Day 3: Grounded RAG, LM Studio and FastAPI

**Date:** 2026-11-23

**Objective:**
Answer student questions only from indexed course material by connecting the
existing embedding/retrieval pipeline to a local Qwen model in LM Studio, then
expose the result through a small FastAPI service with validated requests,
clear errors and source metadata.

### Implemented

- Added `config.py`: one validated, cached settings object loaded from
  environment variables / `.env`. Defaults target LM Studio at
  `http://localhost:1234/v1`, model `qwen3.5-9b`, key `lm-studio`, temperature
  `0.2`, `2048` max tokens and top-k `3`. Invalid values fail early and secrets
  are never logged.
- Replaced the speculative `.env.example` values with the real Day 3 variables
  and removed placeholder services such as PostgreSQL/Pinecone that are not used.
- Added `services/llm_service.py`: a reusable `httpx.Client` that posts
  system/user messages to `/chat/completions`. It supports per-call
  temperature/max-token overrides and distinct errors for connection, timeout,
  HTTP status, invalid JSON, unusable responses and reasoning-only responses.
- Added `pipelines/rag_pipeline.py`: validates input, embeds the query with the
  same MiniLM model used at indexing, retrieves from ChromaDB, builds labelled
  context (`[Source N]`, filename, page, IDs, text), prompts Qwen to answer only
  from that context, and returns `question`, `answer` and `sources`.
- Guaranteed no generation from nothing: empty retrieval returns the explicit
  no-supporting-material answer and `sources=[]` without calling the LLM.
  Sources are built only from retrieved metadata and deduplicated; the model's
  free text is never parsed for citations.
- Added modular `api/` package with Pydantic schemas, `/health`, `/ask`,
  `/docs`, 400 for invalid pipeline input, 422 for request-validation errors
  and 502 for LLM failures. Unknown request fields are forbidden.
- Cached the RAG pipeline with `lru_cache`, so the embedding model, ChromaDB
  client and HTTP client are created once per process rather than per request.
  `/health` reports `llm_status: "not_checked"` instead of claiming an LLM probe.
- Added `scripts/test_rag.py` for a manual full-pipeline check.
- Added 56 new mocked tests for configuration, LLM HTTP behaviour, RAG
  orchestration and FastAPI endpoints. No test requires LM Studio or a model
  download.
- Added `httpx>=0.27.0` as a runtime dependency and updated README,
  architecture, decisions and test documentation.

### Verification (actual console results)

All commands were run from the repository root with the `.venv` Python
(`C:\...\.venv\Scripts\python.exe`). The system-wide `python` is 3.14.0 and does
not have the project dependencies installed.

| Command | Result |
| --- | --- |
| `.venv\Scripts\python.exe -m pytest -v` | **84 passed in 24.03s** |
| `.venv\Scripts\python.exe -m pip check` | `No broken requirements found.` |
| `GET http://localhost:1234/v1/models` via httpx | HTTP 200; `qwen3.5-9b` listed |
| `.venv\Scripts\python.exe scripts/test_rag.py --question "...backpropagation..." --top-k 3` | Grounded answer + 3 sources from `deep_learning.pdf` pages 4 and 5 |
| Live uvicorn `GET /health` | HTTP 200; `{"status":"ok","version":"0.1.0","llm_status":"not_checked"}` |
| Live uvicorn `GET /docs` | HTTP 200; Swagger UI present |
| Live uvicorn `POST /ask` | HTTP 200; 962-character answer, 3 sources, first source `deep_learning.pdf`, page 5, `deep_learning_p5_c0000` |

Excerpt from the real `test_rag.py` answer:

```text
Backpropagation is a technique used during training to adjust parameters so
that they minimize the loss [Source 2]. It works by applying the chain rule of
calculus to compute the gradient of the loss with respect to every parameter
efficiently. This calculation happens in a single backward sweep through the
network [Source 2].

Sources:
  - deep_learning.pdf, page 4 (chunk=deep_learning_p4_c0002)
  - deep_learning.pdf, page 5 (chunk=deep_learning_p5_c0000)
  - deep_learning.pdf, page 4 (chunk=deep_learning_p4_c0001)
```

The answer also states the update rule `theta = theta - eta * gradient` and
attributes it to `[Source 2]`, confirming that retrieved context reached the
model and that metadata-derived references survived the round trip.

### Issues found and resolved

- The first real LM Studio call failed with
  `LLMResponseError: LM Studio response contains no assistant text`. Inspection
  showed `qwen3.5-9b` returned an empty `content` and a populated
  `reasoning_content` when `max_tokens=1024`. The model consumed the budget on
  reasoning. The default was raised to `2048`; a 2048-token test returned
  `content: "4"` for `2+2`. The service now gives a specific error for a
  reasoning-only response instead of returning hidden reasoning as the answer.
- `AskRequest.top_k` initially defaulted to `3` in the schema, which would have
  silently overridden `RETRIEVAL_TOP_K`. It is now `None`, so the pipeline uses
  configuration unless the caller supplies a value.
- `httpx` base-URL joining was checked explicitly: base URL `.../v1` plus
  relative path `/chat/completions` produces `/v1/chat/completions`.
- The first mocked HTTP test failed because the fake client factory did not
  record constructor arguments; the helper was corrected.

### Not implemented in this milestone

Frontend, authentication, streaming answers, retrieval/answer benchmarks, OCR,
PostgreSQL, HDFS, distributed Spark clusters, LangChain, cloud deployment and
production/distributed claims.

### Next milestone

Build a small relevance/groundedness benchmark so retrieval and answer quality
can be measured instead of only inspected manually; then consider a minimal UI.

---

## Milestone 1 — Day 2: Document Processing, Chunking, Embeddings and Retrieval

**Date:** 2026-11-19

**Objective:**
Turn raw PDFs into retrievable, source-attributed chunks using a modular MVP:
PyMuPDF extraction, conservative cleaning, per-page chunking, a local Spark
DataFrame transformation, pretrained embeddings and a persistent ChromaDB
collection.

### Implemented

- Relocated the working Day 1 PDF loader from the repository root
  (`data/pdf_loader.py`) into `src/university_knowledge_assistant/data/` and
  improved its validation and documentation.
- Added conservative whitespace cleaning (`preprocessing/text_cleaner.py`).
- Added per-page character chunking with configurable size/overlap,
  deterministic chunk IDs and parameter validation (`preprocessing/chunker.py`).
- Added a local PySpark DataFrame pipeline that filters empty chunks, selects
  and transforms columns, counts documents/pages/chunks and returns
  embedding-ready records (`pipelines/document_pipeline.py`). The Spark
  environment helper was extracted to `utils/spark_env.py` and reused by the
  Day 1 smoke test.
- Added a Sentence Transformers wrapper that loads `all-MiniLM-L6-v2` once,
  defaults to CPU and encodes batches (`models/embedding_model.py`).
- Added a persistent ChromaDB wrapper with `upsert`-based duplicate prevention,
  explicit embeddings and metadata-preserving top-k search
  (`retrieval/vector_store.py`).
- Added the end-to-end scripts `scripts/index_documents.py` and
  `scripts/test_retrieval.py`, plus unit/integration tests for every component.
- Updated architecture, decisions, README, scripts and tests documentation and
  corrected `.gitignore` so the `src/.../models/` package is not ignored.

### Verification (actual console results)

All commands were run from the repository root with the `.venv` Python
(`C:\...\.venv\Scripts\python.exe`). The system-wide `python` on this machine is
3.14.0 and does not have the project dependencies installed.

| Command | Result |
| --- | --- |
| `.venv\Scripts\python.exe -m pytest -v` | **28 passed in 24.16s** |
| `.venv\Scripts\python.exe scripts/index_documents.py` | 1 PDF, 15 pages, 48 chunks, 48 vectors indexed |
| Re-running `index_documents.py` | Exit code 0; vector count stayed at 48 (upsert is idempotent) |
| `.venv\Scripts\python.exe scripts/test_retrieval.py` | 3 chunks returned from pages 1, 3 and 5 with correct file metadata |
| `.venv\Scripts\python.exe -m pip check` | `No broken requirements found.` |

Indexing summary printed:

```
PDFs found: 1
PDFs processed successfully: 1
Pages extracted: 15
Chunks after Spark filtering: 48
Vectors written in this run: 48
Indexed vectors in ChromaDB: 48
```

The sample question was: *"What is deep learning and how does a neural network
learn?"* Result 1 came from page 1 (guide overview), result 2 from page 3
(introduction to deep learning) and result 3 from page 5 (backpropagation and
gradient descent), which confirms that page references survive the pipeline.

### Issues found and resolved

- The existing PDF loader and Spark smoke test were untracked files at the
  repository root; the loader was moved into the package instead of duplicated.
- `.gitignore` had a root-agnostic `models/` rule that would have hidden the new
  `src/university_knowledge_assistant/models/` package. It is now `/models/`.
- ChromaDB 1.x defaults to its own embedding function; we pass
  `embedding_function=None` and supply vectors from Sentence Transformers so
  indexing and querying always use the same model.
- Spark on Windows logs harmless `winutils.exe`/native-library warnings. The
  local DataFrame pipeline still works and the session is always stopped.

### Not implemented in this milestone

LLM answer generation, LM Studio/Qwen integration, FastAPI, frontend, OCR,
PostgreSQL, HDFS, distributed Spark clusters, LangChain, cloud deployment.

---

## Milestone 0 — Project Initialization

**Date:** 2026-10-05

**Objective:**
Initialize the project repository and establish the foundation for the AI
university knowledge assistant.

### Completed

- Repository initialized with professional structure
- Project structure created following data science best practices
- Initial documentation created (README, scope, architecture)
- Project scope defined with clear objectives and boundaries
- Preliminary architecture documented with planned components
- Development roadmap established with clear phases
- Decision log initialized
- Testing foundation created
- Environment configuration templates created
- Git repository initialized

### Next Milestone (historical plan)

Data discovery, dataset definition and sample document collection — partly
superseded by the Day 2 milestone, which implemented the processing pipeline
against the sample `deep_learning.pdf`.

---

## Roadmap status

| Phase | Status |
| --- | --- |
| 0. Project initialization | Done |
| 1. Data discovery / sample PDF | Done |
| 2. Document processing + vector retrieval (Day 2) | Done |
| 3. RAG answer generation with LM Studio (Day 3) | Done |
| 4. FastAPI service (Day 3) | Done |
| 5. Retrieval / groundedness evaluation benchmark | Planned |
| 6. Frontend / deployment | Planned |

---

**Version:** 0.3.0 (milestone documentation)
**Last Updated:** 2026-11-23
