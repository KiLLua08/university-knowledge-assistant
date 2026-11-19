# AI-Powered University Knowledge Assistant

## Status

🟢 **Day 2 milestone implemented:** PDF extraction, cleaning, chunking, a local
Spark DataFrame pipeline, pretrained embeddings, persistent ChromaDB indexing
and semantic retrieval demos.

This is a learning MVP, not a production system. There is no LLM answer
generation, API or frontend yet.

## Overview

The assistant helps university students find relevant passages in their course
PDFs. Today it indexes PDFs into a local vector store and returns the most
relevant chunks with **file and page references**. Answers grounded in those
chunks are planned for a later milestone.

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
```

See [docs/architecture.md](docs/architecture.md) for the detailed data flow and
rationale, [docs/decisions.md](docs/decisions.md) for technical choices, and
[docs/development_log.md](docs/development_log.md) for progress.

## Requirements

- Windows 11, Python 3.11.9, Java 17
- PyMuPDF, PySpark 4.x, Sentence Transformers, ChromaDB (installed via the project)
- Optional GPU is not required; CPU is the default embedding device

## Setup

```powershell
# From the repository root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Place your own PDFs in `data/raw/` (ignored by Git). A 15-page sample
`deep_learning.pdf` is used for local testing and is **not committed**.

## Usage

```powershell
# Run all automated tests
python -m pytest -v

# Extract, clean, chunk, process with Spark, embed and index every PDF
python scripts/index_documents.py

# Retrieve the top 3 chunks for a sample question
python scripts/test_retrieval.py

# Optional: customise a run
python scripts/index_documents.py --chunk-size 800 --chunk-overlap 100 --device cpu
python scripts/test_retrieval.py --question "What is backpropagation?" --top-k 3
```

The first indexing run downloads the ~90 MB MiniLM model from Hugging Face.
Later runs reuse the local cache. Indexing prints PDF, page, chunk and vector
counts; retrieval prints each chunk's text, filename and page number.

## Repository structure

```
src/university_knowledge_assistant/
├── data/           # PDF extraction (pdf_loader.py)
├── preprocessing/  # text_cleaner.py, chunker.py
├── pipelines/      # local PySpark DataFrame pipeline
├── models/         # Sentence Transformers embedding wrapper
├── retrieval/      # ChromaDB vector store
└── utils/          # shared Spark environment helper
scripts/
├── index_documents.py          # end-to-end indexing
├── test_retrieval.py           # manual retrieval check
└── spark_smoke_test.py         # Day 1 environment check
tests/                          # pytest suite
docs/                           # architecture, log and decisions
data/raw/                       # local PDFs (Git-ignored)
data/chroma/                    # ChromaDB persistence (Git-ignored)
```

## Day 2 test results

`python -m pytest -v` → **28 passed**.

Indexing the sample PDF produced 15 pages, 48 chunks and 48 indexed vectors.
`test_retrieval.py` returned 3 chunks with page metadata. Exact console output
is recorded in [docs/development_log.md](docs/development_log.md).

## Planned (not implemented)

- RAG answer generation with a local Qwen model through LM Studio
- FastAPI service and simple UI
- Source-cited natural-language answers
- OCR for scanned PDFs, hybrid search, evaluation benchmarks
- PostgreSQL metadata and larger-scale distributed processing

## Academic objectives

This project is a practical way to study Deep Learning, NLP, Transformers,
Information Retrieval, Big Data processing, data engineering, software testing
and system architecture.

## Documentation

- [Project Scope](docs/project_scope.md)
- [Architecture](docs/architecture.md)
- [Development Log](docs/development_log.md)
- [Decisions](docs/decisions.md)

## Data and licensing

Do not commit university PDFs or other copyrighted course material: `data/raw/`
and `data/chroma/` are Git-ignored. The repository's own license is to be
determined.
