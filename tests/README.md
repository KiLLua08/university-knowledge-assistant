# Tests

The suite is intentionally fast and offline: model loading, LLM HTTP calls and
retrieval are mocked, and ChromaDB uses `tmp_path` directories. FastAPI endpoints
are exercised with `TestClient`. Only the Spark test starts a real local session
(about 20–24 seconds for the whole suite).

No test requires LM Studio, an API key, a downloaded model or a committed PDF.

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
| `test_config.py` | Defaults, env overrides, caching, numeric and value validation |
| `test_llm_service.py` | Request payload, overrides, timeout/connection/HTTP/JSON errors, reasoning-only response |
| `test_rag_pipeline.py` | Prompt context, metadata sources, deduplication, empty retrieval, validation, cached dependencies |
| `test_api.py` | `/health`, `/ask`, `/docs`, validation errors, 400/422/502 status codes |

## Running

```bash
python -m pytest -v
python -m pytest tests/test_rag_pipeline.py tests/test_api.py -v
```

PDF fixtures and ChromaDB databases are created in temporary directories and
removed after each test. LLM responses are fake Chat Completion payloads; the
Authorization header is asserted but no real secret is used.
