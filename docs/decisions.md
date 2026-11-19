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

## Future Decisions
Decisions still to make in later milestones:
- LLM selection and LM Studio/Qwen integration
- RAG context assembly and answer-citation format
- Retrieval evaluation metrics and benchmark dataset
- API design with FastAPI
- PostgreSQL metadata storage (if needed)
- Frontend framework and deployment strategy

---

**Version:** 0.2.0
**Last Updated:** 2026-11-19
