# Tests

The suite is intentionally fast and offline: model loading is mocked and
ChromaDB uses `tmp_path` directories. Only the Spark test starts a real local
session (about 20 seconds for the whole suite).

## Files

| File | What it covers |
| --- | --- |
| `test_package.py` | Package import and version |
| `test_pdf_loader.py` | PyMuPDF extraction, page metadata, empty pages, validation |
| `test_text_cleaner.py` | Whitespace normalization without destroying notation |
| `test_chunker.py` | Chunking, overlap, metadata, unique/deterministic IDs, invalid parameters |
| `test_spark_pipeline.py` | Spark filtering, column transformation and counts |
| `test_embedding_model.py` | Model loading args, embedding shape/type, empty input (mocked) |
| `test_vector_store.py` | ChromaDB upsert idempotency, retrieval metadata, `top_k` |

## Running

```bash
python -m pytest -v
python -m pytest tests/test_chunker.py -v
```

PDF fixtures and ChromaDB databases are created in temporary directories and
removed after each test. No real PDFs or downloaded models are required.
