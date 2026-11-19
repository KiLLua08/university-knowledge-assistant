# Scripts

Executable entry points for the implemented MVP. Run them from the repository
root with the project's `.venv` Python active.

## `index_documents.py`

End-to-end indexing: discovers every PDF directly in `data/raw/`, extracts
pages with PyMuPDF, cleans text, chunks each page, runs the local Spark
DataFrame pipeline, embeds chunks with `all-MiniLM-L6-v2` and upserts them
into the persistent ChromaDB collection at `data/chroma/`.

```bash
python scripts/index_documents.py
python scripts/index_documents.py --chunk-size 800 --chunk-overlap 100 --device cpu
```

Prints the number of PDFs, pages, chunks and indexed vectors. A PDF that fails
to process is reported on stderr and makes the script exit with a non-zero
code; it is never silently skipped.

## `test_retrieval.py`

Loads an existing collection, embeds a sample deep-learning question with the
same model, and prints the top 3 chunks with filename, page number, document
ID, chunk ID and distance.

```bash
python scripts/test_retrieval.py
python scripts/test_retrieval.py --question "What is backpropagation?" --top-k 3
```

Exits with an error if the collection has not been created yet.

## `spark_smoke_test.py`

Day 1 environment check: starts a local Spark session, creates a small
DataFrame and applies a filter and aggregation. It now reuses the shared
`prepare_spark_environment()` helper from the package.

```bash
python scripts/spark_smoke_test.py
```
