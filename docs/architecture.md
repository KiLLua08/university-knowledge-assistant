# System Architecture

**Status: Day 2 milestone implemented (MVP).** Last updated 2026-11-19.

This document describes the architecture that is **actually running** in the
repository, and clearly separates it from components that are only planned.

---

## 1. Implemented components

| Layer | Component | Status | File |
| --- | --- | --- | --- |
| Ingestion | PyMuPDF page extraction | Implemented | `src/university_knowledge_assistant/data/pdf_loader.py` |
| Preprocessing | Conservative whitespace cleaning | Implemented | `src/university_knowledge_assistant/preprocessing/text_cleaner.py` |
| Preprocessing | Character chunking with overlap | Implemented | `src/university_knowledge_assistant/preprocessing/chunker.py` |
| Big data | Local Spark DataFrame pipeline | Implemented | `src/university_knowledge_assistant/pipelines/document_pipeline.py` |
| Models | Pretrained sentence embeddings | Implemented | `src/university_knowledge_assistant/models/embedding_model.py` |
| Retrieval | Persistent ChromaDB store + search | Implemented | `src/university_knowledge_assistant/retrieval/vector_store.py` |
| Scripts | Indexing and retrieval demos | Implemented | `scripts/index_documents.py`, `scripts/test_retrieval.py` |
| Tests | 28 automated tests | Implemented | `tests/` |

### Planned components (not implemented here)

FastAPI, LLM answer generation (local Qwen through LM Studio), RAG context
assembly, source-cited answers, PostgreSQL metadata storage, hybrid/keyword
search, OCR, frontend, authentication, Docker/Kubernetes/cloud deployment and
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

### Actual query data flow

```
Question string
    |
    |  load_embedding_model()  (same model name and device as indexing)
    |  embed_texts([question])            models/embedding_model.py
    v
Query vector
    |
    |  VectorStore.search(query_vector, top_k=3)
    v
Top 3 chunks + {filename, page_number, document_id, chunk_id} + distance
```

Entry point: `python scripts/test_retrieval.py`. There is **no answer
generation** step: the script displays retrieved evidence only.

---

## 3. Design rationale

### Why page-level metadata is preserved

A page number is the smallest unit a student can meaningfully cite. If we
flattened a PDF into one string early, we could not tell later which page a
chunk came from. Every record therefore carries `document_id`, `filename` and
a 1-based `page_number`, and every chunk inherits them. ChromaDB stores them
as metadata, so retrieval results can be shown as "deep_learning.pdf, page 7".
This is the foundation for the future source-attribution requirement of the
RAG system.

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
it is small, fast on CPU, widely used for semantic search, and suitable for a
8 GB GPU machine where LM Studio may need VRAM later. The model is loaded once
per process and reused for all chunks and for the query. It is **not**
fine-tuned in this milestone. CPU is the safe default; `--device cuda` is
available for experimentation.

### Why ChromaDB

ChromaDB gives us a local, persistent vector store with metadata filtering and
similarity search without running a service. This keeps the MVP offline, free
and easy to inspect. The store is created with `embedding_function=None`
because embeddings are supplied explicitly by our Sentence Transformers model;
this prevents ChromaDB from silently using a different embedding model for
queries. No remote vector database is used.

### How Spark is used in this MVP

The Spark component is a teaching tool for a real DataFrame transformation
pipeline: it creates a DataFrame with an explicit schema from the extracted
records, filters blank text, selects and renames the embedding-ready columns,
adds a derived `text_length` column, and performs `count()` and `distinct()`
actions before collecting the small result to the driver. It runs with
`local[2]` on one laptop. **This is not a production distributed cluster** and
the dataset is far too small to benefit from distribution. The same code shape
could later operate on larger datasets, but no HDFS, cluster manager or cloud
storage is part of this milestone.

---

## 4. Explicitly not implemented

- No OCR: scanned/image-only PDFs produce empty pages and are skipped at chunking.
- No LLM/RAG answer generation, no LM Studio integration yet.
- No FastAPI, frontend, authentication or session management.
- No PostgreSQL, HDFS, Kubernetes or cloud deployment.
- No LangChain; the pipeline is plain, readable Python.
- No distributed Spark execution, no Spark cluster and no performance tuning.

---

## 5. Known limitations

- Character-based chunking can split a formula, table or code block mid-line.
- ChromaDB's default distance is L2; vectors are unit-normalized, so ranking is
  equivalent to cosine similarity for this MVP.
- Only PDFs directly inside `data/raw/` are discovered.
- Re-indexing detects duplicates by `chunk_id`; changing the document stem
  creates new IDs rather than updating old ones.
- Retrieval is evaluated by manual inspection, not with a relevance benchmark.
- The MiniLM model is downloaded from Hugging Face on first run (~90 MB).

---

## 6. Running the implemented pipeline

From the repository root, with the `.venv` Python active:

```bash
python -m pytest -v
python scripts/index_documents.py
python scripts/test_retrieval.py
```

`index_documents.py` prints PDF, page, chunk and indexed-vector counts.
`test_retrieval.py` prints the top 3 chunks with file and page metadata.
