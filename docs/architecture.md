# System Architecture

**Status: Day 3 milestone implemented (MVP).** Last updated 2026-11-23.

This document describes the architecture that is **actually running** in the
repository, and clearly separates it from components that are only planned.

---

## 1. Implemented components

| Layer | Component | Status | File |
| --- | --- | --- | --- |
| Configuration | Validated cached settings from env / `.env` | Implemented | `src/university_knowledge_assistant/config.py` |
| Ingestion | PyMuPDF page extraction | Implemented | `src/university_knowledge_assistant/data/pdf_loader.py` |
| Preprocessing | Conservative whitespace cleaning | Implemented | `src/university_knowledge_assistant/preprocessing/text_cleaner.py` |
| Preprocessing | Character chunking with overlap | Implemented | `src/university_knowledge_assistant/preprocessing/chunker.py` |
| Big data | Local Spark DataFrame pipeline | Implemented | `src/university_knowledge_assistant/pipelines/document_pipeline.py` |
| Models | Pretrained sentence embeddings | Implemented | `src/university_knowledge_assistant/models/embedding_model.py` |
| Retrieval | Persistent ChromaDB store + search | Implemented | `src/university_knowledge_assistant/retrieval/vector_store.py` |
| Services | LM Studio OpenAI-compatible HTTP client | Implemented | `src/university_knowledge_assistant/services/llm_service.py` |
| RAG | Context assembly, grounding prompt, source deduplication | Implemented | `src/university_knowledge_assistant/pipelines/rag_pipeline.py` |
| API | FastAPI `/health`, `/ask`, `/docs` | Implemented | `src/university_knowledge_assistant/api/` |
| Scripts | Indexing, retrieval and RAG demos | Implemented | `scripts/index_documents.py`, `scripts/test_retrieval.py`, `scripts/test_rag.py` |
| Tests | 84 automated tests | Implemented | `tests/` |

### Planned components (not implemented here)

Retrieval relevance benchmarks, OCR, hybrid/keyword search, PostgreSQL metadata
storage, frontend, authentication, Docker/Kubernetes/cloud deployment and
distributed Spark clusters. None of these are claimed as working today.

---

## 2. Actual indexing data flow

```
data/raw/*.pdf
    |
    |  extract_pdf()                      data/pdf_loader.py
    v
Page records: {document_id, filename, page_number, text}
    |
    |  clean_text() per page              preprocessing/text_cleaner.py
    v
Cleaned page records (same metadata)
    |
    |  chunk_pages() per page             preprocessing/chunker.py
    v
Chunk records: {..., chunk_id, chunk_index, text}
    |
    |  process_chunks()                   pipelines/document_pipeline.py
    |  Spark: filter -> select -> withColumn -> distinct counts -> collect
    v
Embedding-ready records + counts
    |
    |  load_embedding_model() once
    |  embed_texts()                      models/embedding_model.py
    v
Vectors (one per chunk)
    |
    |  VectorStore.upsert_chunks()        retrieval/vector_store.py
    v
data/chroma/  (persistent local ChromaDB collection)
```

Entry point: `python scripts/index_documents.py`.

### Actual retrieval-only data flow

```
Question string
    |
    |  load_embedding_model()  (same model name and device as indexing)
    |  embed_texts([question])            models/embedding_model.py
    v
Query vector
    |
    |  VectorStore.search(query_vector, top_k)
    v
Top-k chunks + {filename, page_number, document_id, chunk_id} + distance
```

Entry point: `python scripts/test_retrieval.py`. This script still displays
evidence only.

### Actual RAG answer data flow

```
Question + optional top_k
    |
    |  RAGPipeline.answer()               pipelines/rag_pipeline.py
    |    - validate non-empty question and positive integer top_k
    |    - embed query with the SAME MiniLM model used for indexing
    |    - VectorStore.search()           retrieval/vector_store.py
    v
Retrieved chunks or empty list
    |
    |  if empty -> NO_CONTEXT_ANSWER, sources=[], no LLM call
    |  else -> build_context() with [Source N], filename, page, IDs and text
    |       -> build_user_prompt(question, context)
    |       -> LLMService.generate_answer(SYSTEM_PROMPT, user_prompt)
    v
LM Studio qwen3.5-9b via POST /v1/chat/completions
    |
    v
{question, answer, sources}
    |
    |  build_sources() reads ONLY retrieved metadata and deduplicates it
    v
Grounded answer with file/page references
```

Entry points: `scripts/test_rag.py` and `POST /ask`.

### Actual API data flow

```
HTTP client
    |
    |  GET /health  -> {status, version, llm_status: "not_checked"}
    |  GET /docs    -> FastAPI Swagger UI
    |  POST /ask    -> AskRequest(question, top_k?)
    v
FastAPI route                              api/routes.py
    |
    |  Depends(get_rag_pipeline)            api/dependencies.py
    |  one cached RAGPipeline per process; model/HTTP client reused
    v
RAGPipeline.answer()
    |
    |  ValueError -> 400
    |  LLMError   -> 502
    |  success    -> AskResponse 200
    v
{question, answer, sources}
```

The API route contains no business logic and does not parse citations out of
the model's free text.

---

## 3. Design rationale

### Why page-level metadata is preserved

A page number is the smallest unit a student can meaningfully cite. Every
record carries `document_id`, `filename` and a 1-based `page_number`; every
chunk inherits them. ChromaDB stores them as metadata, so RAG can return
"deep_learning.pdf, page 5" without trusting the LLM.

### Why chunking is needed

Embedding models have a limited context window, and a whole 15-page chapter
would produce one vague vector. Chunks of ~1000 characters keep each vector
focused on one idea. A 150-character overlap reduces the chance that a sentence
split across a boundary loses its context. Chunking is done **per page**, so a
chunk never mixes text from two pages. IDs such as `deep_learning_p4_c0000`
are deterministic, which makes re-indexing idempotent via ChromaDB `upsert`.

### What embeddings are and why we chose this model

An embedding is a numerical vector representing the meaning of a text; texts
with similar meanings lie close together in that vector space. We use the
pretrained `sentence-transformers/all-MiniLM-L6-v2` model (384 dimensions):
it is small, fast on CPU and suitable for a machine where LM Studio may need
VRAM. The model is loaded once per process and reused for chunks and queries.
It is **not** fine-tuned in this milestone. CPU is the safe default.

### Why ChromaDB

ChromaDB gives us a local, persistent vector store with metadata and
similarity search without running a service. The store is created with
`embedding_function=None` because embeddings are supplied explicitly by our
Sentence Transformers model; this prevents ChromaDB from silently using a
different embedding model for queries. No remote vector database is used.

### How Spark is used in this MVP

The Spark component is a teaching tool for a real DataFrame transformation
pipeline: it creates a DataFrame with an explicit schema from the extracted
records, filters blank text, selects and renames the embedding-ready columns,
adds a derived `text_length` column, and performs `count()` and `distinct()`
actions before collecting the small result to the driver. It runs with
`local[2]` on one laptop. **This is not a production distributed cluster**.

### Why LM Studio through an OpenAI-compatible HTTP client

LM Studio already hosts models locally and exposes `/v1/chat/completions`, so
the project uses ordinary `httpx` calls instead of loading a second copy of a
large model in Python. `LLMService` sends system/user messages, the configured
model ID, temperature, max tokens and a timeout. It raises distinct errors for
connection, timeout, HTTP status and invalid-response failures. The API key is
only placed in the request header and never logged.

`qwen3.5-9b` is a reasoning model: LM Studio returns a separate
`reasoning_content` field. The default `LLM_MAX_TOKENS=2048` leaves room for the
final `content`; a reasoning-only response is reported as a clear error rather
than used as the answer.

### Why sources come from metadata, not the LLM

The system prompt tells Qwen to answer only from retrieved context and to admit
when evidence is insufficient. Even so, model text is untrusted. `build_sources()`
constructs every returned source from ChromaDB metadata and deduplicates
identical chunks. If retrieval returns nothing, the pipeline never calls the
LLM and returns an explicit no-evidence answer with an empty source list.

### Why centralized configuration

`config.py` is the single place for URLs, model IDs, thresholds and paths.
`Settings.from_env()` validates values, and `get_settings()` is cached so the
environment is read once per process rather than on every request. `.env` is
ignored by Git; `.env.example` documents the required variables.

### Why the API is small

FastAPI gives automatic request validation and OpenAPI docs with little code.
`get_rag_pipeline()` is cached with `lru_cache`, so the embedding model,
ChromaDB client and HTTP client are not recreated per request. Pydantic schemas
forbid unknown request fields and constrain `question` and `top_k`. `/health`
deliberately does **not** probe LM Studio; it reports `llm_status:
"not_checked"` to avoid an invented health claim.

---

## 4. Explicitly not implemented

- No OCR: scanned/image-only PDFs produce empty pages and are skipped at chunking.
- No relevance benchmark for retrieval or answer quality.
- No frontend, authentication, session management or rate limiting.
- No PostgreSQL, HDFS, Kubernetes or cloud deployment.
- No LangChain; the pipeline is plain, readable Python.
- No distributed Spark execution, no Spark cluster and no performance tuning.
- No streaming responses from LM Studio; one chat completion per `/ask`.

---

## 5. Known limitations

- Character-based chunking can split a formula, table or code block mid-line.
- ChromaDB's default distance is L2; vectors are unit-normalized, so ranking is
  equivalent to cosine similarity for this MVP.
- Only PDFs directly inside `data/raw/` are discovered.
- Re-indexing detects duplicates by `chunk_id`; changing the document stem
  creates new IDs rather than updating old ones.
- Retrieval and answers are evaluated by manual inspection, not with a benchmark.
- The MiniLM model is downloaded from Hugging Face on first run (~90 MB).
- LM Studio must already be running with `qwen3.5-9b` loaded for `/ask` to
  generate an answer; otherwise `/ask` returns 502.
- Qwen's reasoning token usage can vary; increase `LLM_MAX_TOKENS` if only
  reasoning content is returned.
- `/health` is a liveness check only; it does not verify LM Studio.

---

## 6. Running the implemented pipeline

From the repository root, with the `.venv` Python active:

```bash
python -m pytest -v
python scripts/index_documents.py
python scripts/test_retrieval.py
python scripts/test_rag.py --question "What is backpropagation?"
python -m uvicorn university_knowledge_assistant.api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` or call `GET /health` and `POST /ask`.
