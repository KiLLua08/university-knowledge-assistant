# Technical Decisions Log

This document records important technical decisions made throughout the AI-Powered University Knowledge Assistant project. Each decision includes the rationale, alternatives considered, and implications.

---

## Decision 001 — Project Direction

**Date:** 2026-10-05

**Decision:**
Develop an AI-powered university knowledge assistant to help students navigate and understand academic resources.

**Reason:**
- Addresses a real problem faced by university students (difficulty finding information across diverse academic materials)
- Provides comprehensive learning opportunities in Deep Learning, NLP, Big Data, and AI system engineering
- Balances practical application with academic objectives
- Has clear, measurable success criteria

**Alternatives Considered:**
- Generic document Q&A system (rejected - less focused on academic domain)
- Chatbot for general university information (rejected - doesn't leverage academic document processing)
- Research-only project without practical application (rejected - needs practical component)

**Implications:**
- Focus on academic document types (PDFs, lecture notes, exercises, exams)
- Domain-specific considerations (academic terminology, course structure)
- Evaluation metrics tied to educational use cases
- Need for source attribution in answers

**Status:** Accepted

---

## Decision 002 — Project Structure

**Date:** 2026-10-05

**Decision:**
Use a standardized data science project structure with clear separation of concerns.

**Reason:**
- Follows industry best practices for ML/DL projects
- Supports reproducibility and maintainability
- Clear separation between code, data, notebooks, and documentation
- Facilitates collaboration and future extension

**Alternatives Considered:**
- Monolithic structure (rejected - hard to maintain)
- Minimal structure (rejected - doesn't scale well)
- Framework-specific structure (rejected - too opinionated)

**Structure Chosen:**
```
project-root/
├── docs/           # Documentation
├── data/           # Data directories (raw, interim, processed, external)
├── notebooks/      # Jupyter notebooks
├── src/            # Source code
├── tests/          # Test suite
├── scripts/        # Utility scripts
├── experiments/    # Experimental code
└── logs/           # Application logs
```

**Implications:**
- Requires discipline to maintain structure
- Clear onboarding for new contributors
- Easy to identify where to add new code
- Supports automated testing and CI/CD

**Status:** Accepted

---

## Decision 003 — Technology Stack Hypothesis

**Date:** 2026-10-05

**Decision:**
Adopt Python-based technology stack with PyTorch, Hugging Face, and Apache Spark as primary tools.

**Reason:**
- Python is the de facto language for ML/DL
- PyTorch provides flexibility for research and production
- Hugging Face offers state-of-the-art pre-trained models
- Apache Spark handles large-scale data processing
- Strong community support and documentation

**Alternatives Considered:**
- TensorFlow instead of PyTorch (rejected - PyTorch more research-friendly)
- Custom embeddings only (rejected - leverage pre-trained models)
- No Big Data framework initially (rejected - project requires scalability)

**Planned Stack:**
- **Language**: Python
- **Deep Learning**: PyTorch
- **NLP**: Hugging Face Transformers
- **Big Data**: Apache Spark / PySpark
- **Database**: PostgreSQL (metadata) + Vector DB (TBD)
- **API**: FastAPI
- **Containerization**: Docker
- **Version Control**: Git/GitHub
- **Notebooks**: Jupyter

**Implications:**
- Technology choices may evolve based on experimentation
- Vector database selection to be determined during Phase 5
- Requires learning curve for Spark if not familiar
- All tools have strong community support

**Status:** Accepted (subject to change based on experimentation)

---

## Decision 004 — Documentation Strategy

**Date:** 2026-10-05

**Decision:**
Maintain comprehensive documentation including scope, architecture, development log, and decisions.

**Reason:**
- University project requires traceability
- Academic projects need clear documentation of process
- Facilitates future development and maintenance
- Supports reproducibility

**Alternatives Considered:**
- Minimal documentation (rejected - insufficient for academic project)
- Code comments only (rejected - doesn't capture high-level decisions)
- Video documentation (rejected - not searchable, hard to maintain)

**Documentation Structure:**
- `README.md`: Project overview and quick start
- `docs/project_scope.md`: Detailed scope and objectives
- `docs/architecture.md`: System architecture and design
- `docs/development_log.md`: Milestones and progress
- `docs/decisions.md`: Technical decisions (this file)

**Implications:**
- Requires ongoing maintenance
- Must stay synchronized with implementation
- Slows initial development but improves long-term maintainability
- Essential for academic evaluation

**Status:** Accepted

---

## Decision 005 — Git Workflow

**Date:** 2026-10-05

**Decision:**
Use meaningful milestone-based commits with clear commit messages.

**Reason:**
- University project requires traceability
- Clear commit history facilitates understanding of development process
- Supports reproducibility and version management
- No fake history or artificial commit splitting

**Alternatives Considered:**
- Granular commits for every change (rejected - creates noise)
- Feature branch workflow (rejected - single developer, overkill)
- Commit-per-file (rejected - loses context)

**Commit Strategy:**
- One commit per meaningful milestone
- Clear, descriptive commit messages
- Convention: `feat:`, `fix:`, `experiment:`, `chore:`
- No manipulation of Git dates or history

**Implications:**
- Commits may be larger but more meaningful
- Clearer understanding of project evolution
- Easier to review progress
- Honest representation of development

**Status:** Accepted

---

## Decision 006 — PyMuPDF for PDF extraction

**Date:** 2026-11-19

**Decision:**
Use `pymupdf` to extract text page by page and keep `document_id`, `filename`,
`page_number` and `text` on every record.

**Reason:**
The Day 1 smoke test already extracted a 15-page PDF successfully with
PyMuPDF. It is fast, gives direct page access and returns plain text without
an extra service.

**Alternatives Considered:**
- PyPDF2 (rejected: already removed from dependencies, weaker page handling)
- OCR pipelines (rejected for now: unnecessary complexity and no scanned PDFs)

**Implications:**
Scanned pages produce empty text and are skipped later; OCR remains future
work. Page numbers survive all the way into ChromaDB metadata.

**Status:** Accepted

---

## Decision 007 — Conservative text cleaning

**Date:** 2026-11-19

**Decision:**
Normalize line endings, collapse repeated spaces, cap blank lines at one, and
leave words, case, punctuation, tabs and symbols untouched.

**Reason:**
Course documents contain formulas, code and technical notation. Lowercasing,
punctuation removal or stemming would damage exactly the content we want to
retrieve.

**Alternatives Considered:**
- Full NLP normalization with lemmatization (rejected: destructive here)
- No cleaning at all (rejected: PDF layout introduces noisy blank lines)

**Status:** Accepted

---

## Decision 008 — Character chunking with deterministic IDs

**Date:** 2026-11-19

**Decision:**
Chunk each cleaned page into at most 1000 characters with 150 characters of
overlap, using IDs like `deep_learning_p4_c0000`.

**Reason:**
Simple to explain and debug for an MVP. Overlap keeps context across a
boundary. Deterministic IDs let ChromaDB `upsert` make re-indexing idempotent.
Pages are never merged, so page references remain exact.

**Alternatives Considered:**
- Token/transformer-aware chunking (deferred: extra complexity)
- Recursive semantic splitters and LangChain (rejected: unnecessary here)

**Implications:**
A formula or table can still be split mid-line; this is a documented
limitation, not a hidden failure.

**Status:** Accepted

---

## Decision 009 — Pretrained all-MiniLM-L6-v2 on CPU by default

**Date:** 2026-11-19

**Decision:**
Use `sentence-transformers/all-MiniLM-L6-v2`, load it once per process, and
default to CPU with an optional `--device cuda`.

**Reason:**
Small, fast, good general-purpose semantic search quality and no fine-tuning
needed. The RTX 3070 has 8 GB VRAM that LM Studio will need later, so CPU is
the safe default today.

**Alternatives Considered:**
- Larger models (rejected: slower, more VRAM, no demonstrated benefit here)
- Fine-tuning (rejected: no labelled dataset yet)

**Status:** Accepted

---

## Decision 010 — Local persistent ChromaDB with explicit embeddings

**Date:** 2026-11-19

**Decision:**
Use ChromaDB's `PersistentClient` in `data/chroma/` and pass embeddings
explicitly (`embedding_function=None`).

**Reason:**
Local persistence, zero infrastructure and built-in metadata. Supplying our
own vectors guarantees indexing and querying use the exact same model.

**Alternatives Considered:**
- Remote Pinecone/Weaviate (rejected: cost, network, unnecessary for MVP)
- FAISS files (deferred: no metadata/document storage layer provided here)

**Status:** Accepted

---

## Decision 011 — Spark as a local teaching pipeline, not a cluster

**Date:** 2026-11-19

**Decision:**
Run one local Spark session (`local[2]`) that creates a DataFrame from chunk
records, filters empties, transforms columns, computes distinct counts and
collects the small result to the driver.

**Reason:**
The project must demonstrate real Spark DataFrame transformations, but the
sample dataset has one 15-page PDF. Pretending it is a distributed production
system would be misleading.

**Alternatives Considered:**
- Pure Python lists only (rejected: does not exercise the Big Data component)
- Spark cluster/HDFS (rejected: out of scope for this milestone)

**Status:** Accepted

---

## Decision 012 — LM Studio via OpenAI-compatible HTTP

**Date:** 2026-11-23

**Decision:**
Use `httpx` to call LM Studio's `/v1/chat/completions` endpoint with the local
model ID `qwen3.5-9b`, system/user messages, configured temperature/max tokens,
a request timeout and distinct error types.

**Reason:**
LM Studio already hosts the model locally and exposes a stable OpenAI-style
API. Calling it over HTTP avoids loading a second copy of a multi-billion
parameter model inside the Python process and keeps generation separate from
retrieval.

**Alternatives Considered:**
- Loading Qwen with Transformers in-process (rejected: duplicate VRAM/RAM use)
- LangChain LLM wrappers (rejected: unnecessary abstraction for one endpoint)
- Cloud LLM APIs (rejected: course data should stay local; adds cost/secrets)

**Implications:**
LM Studio must be running with `qwen3.5-9b` loaded for `/ask` to generate.
Connection, timeout, HTTP, invalid-JSON and invalid-body failures are reported
clearly. The API key is sent only in the Authorization header and never logged.

**Status:** Accepted

---

## Decision 013 — Centralized validated configuration

**Date:** 2026-11-23

**Decision:**
Read all runtime settings in `config.py` from environment variables / `.env`
and expose one cached `Settings` instance through `get_settings()`.

**Reason:**
Scattering URLs, model names and thresholds across modules makes behaviour hard
to reproduce and risks per-request environment reads. Validation catches bad
numeric values and empty strings at startup.

**Alternatives Considered:**
- Module-level constants with no overrides (rejected: cannot switch endpoints)
- Reading `os.getenv()` in every function (rejected: inconsistent and repeated)
- Committing a populated `.env` (rejected: secret hygiene)

**Implications:**
`.env.example` documents defaults; `.env` stays ignored. Changing settings in a
running process requires a restart, which is acceptable for this MVP.

**Status:** Accepted

---

## Decision 014 — Metadata-derived sources and no-generation-on-empty-retrieval

**Date:** 2026-11-23

**Decision:**
Build every returned source from retrieved ChromaDB metadata and deduplicate
it. If retrieval returns no chunks, return a fixed no-supporting-material
answer with `sources=[]` and do not call the LLM.

**Reason:**
A language model can confidently invent filenames, pages and citations. The
system prompt asks for grounded behaviour, but the API contract must not depend
on model compliance. Generating from an empty context would be ungrounded by
definition.

**Alternatives Considered:**
- Parsing citations from the LLM answer (rejected: untrusted and fragile)
- Always calling the LLM, even with empty context (rejected: invites hallucination)
- Returning only chunk text without metadata (rejected: poor source attribution)

**Implications:**
Answers can refer to `[Source N]` labels in the prompt context, but source
objects are produced independently from metadata. The pipeline is honest when
the index has no evidence.

**Status:** Accepted

---

## Decision 015 — Small modular FastAPI with one cached pipeline

**Date:** 2026-11-23

**Decision:**
Expose `GET /health`, `POST /ask` and `GET /docs` from an `api/` package with
Pydantic schemas and an `lru_cache`-backed RAG pipeline dependency. `/health`
reports `llm_status: "not_checked"` rather than probing LM Studio.

**Reason:**
FastAPI provides automatic validation and OpenAPI docs with minimal code.
Caching the pipeline avoids reloading MiniLM or recreating ChromaDB/HTTP
clients per request. A liveness endpoint must not claim a dependency is healthy
without checking it.

**Alternatives Considered:**
- Plain `http.server` handlers (rejected: no validation or docs)
- Building the pipeline inside each route call (rejected: repeated heavy init)
- A deep LLM health probe in `/health` (rejected: slow and would misreport state)

**Implications:**
Invalid request bodies return 422, pipeline value errors return 400, and LLM
failures return 502. Streaming, auth and rate limiting are intentionally absent
from this MVP.

**Status:** Accepted

---

## Decision 016 — Larger token budget for Qwen reasoning

**Date:** 2026-11-23

**Decision:**
Default `LLM_MAX_TOKENS` to `2048` and reject responses that contain only
`reasoning_content` with a specific `LLMResponseError`.

**Reason:**
Real integration showed `qwen3.5-9b` returning empty `content` at 1024 tokens
because it spent the budget on internal reasoning. At 2048 tokens it produced
the final answer. Returning `reasoning_content` as the answer would be wrong.

**Alternatives Considered:**
- Keeping 1024 and parsing reasoning text (rejected: not the user-facing answer)
- Disabling reasoning in LM Studio settings (rejected: out-of-scope model config)
- Hardcoding an even larger budget (rejected: 2048 is configurable and worked)

**Implications:**
Users can override `LLM_MAX_TOKENS` in `.env`; a reasoning-only response now
gives an actionable error instead of an empty or misleading answer.

**Status:** Accepted

---

## Future Decisions
Decisions still to make in later milestones:
- Retrieval relevance and groundedness evaluation metrics / benchmark dataset
- PostgreSQL metadata storage (if needed)
- Frontend framework, streaming UX and deployment strategy
- Authentication and multi-user behaviour (if ever required)

---

**Version:** 0.3.0
**Last Updated:** 2026-11-23
