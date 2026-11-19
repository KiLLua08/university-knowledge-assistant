# Development Log

This document tracks the development milestones and progress of the AI-Powered
University Knowledge Assistant project.

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

### Next milestone

Retrieval-augmented answer generation with source citations, followed by a
FastAPI service. Before that, a small relevance benchmark should be created so
retrieval quality can be measured instead of only inspected manually.

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
superseded by the Day 2 milestone above, which implemented the processing
pipeline against the sample `deep_learning.pdf`.

---

## Roadmap status

| Phase | Status |
| --- | --- |
| 0. Project initialization | Done |
| 1. Data discovery / sample PDF | Done |
| 2. Document processing + vector retrieval (Day 2) | Done |
| 3. Retrieval evaluation benchmark | Planned |
| 4. RAG answer generation with LM Studio | Planned |
| 5. FastAPI service | Planned |
| 6. Frontend / deployment | Planned |

---

**Version:** 0.2.0
**Last Updated:** 2026-11-19
