"""Index every PDF in data/raw into the local ChromaDB collection.

Run from the repository root with ``python scripts/index_documents.py``.
The virtual environment's Python must be active (see README).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

# Make ``import university_knowledge_assistant`` work even when the package
# has not been installed with ``pip install -e .``.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from university_knowledge_assistant.data import extract_pdf
from university_knowledge_assistant.models import (
    DEFAULT_DEVICE,
    DEFAULT_MODEL_NAME,
    embed_texts,
    load_embedding_model,
)
from university_knowledge_assistant.pipelines import process_chunks
from university_knowledge_assistant.preprocessing import chunk_pages, clean_text
from university_knowledge_assistant.retrieval import VectorStore
from university_knowledge_assistant.utils import prepare_spark_environment

DEFAULT_RAW_DIR = REPO_ROOT / "data" / "raw"
DEFAULT_PERSIST_DIR = REPO_ROOT / "data" / "chroma"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--persist-directory", type=Path, default=DEFAULT_PERSIST_DIR)
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=150)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    prepare_spark_environment()

    raw_dir: Path = args.raw_dir
    if not raw_dir.is_dir():
        print(f"[ERROR] Raw data directory does not exist: {raw_dir}", file=sys.stderr)
        return 1

    pdf_paths = sorted(raw_dir.glob("*.pdf"))
    if not pdf_paths:
        print(f"[ERROR] No PDF files found in {raw_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(pdf_paths)} PDF file(s) in {raw_dir}", flush=True)

    page_records: list[dict[str, object]] = []
    chunk_records: list[dict[str, object]] = []
    failed_pdfs: list[str] = []
    empty_pages = 0

    for pdf_path in pdf_paths:
        try:
            pages = extract_pdf(pdf_path)
            cleaned_pages = []
            for page in pages:
                cleaned_text = clean_text(page["text"])
                if not cleaned_text:
                    empty_pages += 1
                cleaned_pages.append({**page, "text": cleaned_text})

            chunks = chunk_pages(
                cleaned_pages,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
            )
        except Exception as exc:
            failed_pdfs.append(pdf_path.name)
            print(
                f"[ERROR] Could not process {pdf_path.name}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            continue

        page_records.extend(cleaned_pages)
        chunk_records.extend(chunks)
        print(
            f"  {pdf_path.name}: {len(pages)} page(s), {len(chunks)} chunk(s)",
            flush=True,
        )

    if not chunk_records:
        print("[ERROR] No non-empty chunks were produced; nothing to index.", file=sys.stderr)
        return 1

    try:
        result = process_chunks(chunk_records)
    except Exception as exc:
        print(f"[ERROR] Spark processing failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(
        f"Spark processed {result.chunk_count} chunk(s) from "
        f"{result.document_count} document(s) / {result.page_count} page(s).",
        flush=True,
    )

    print(f"Loading embedding model '{args.model_name}' on {args.device}...", flush=True)
    try:
        model = load_embedding_model(args.model_name, args.device)
    except Exception as exc:
        print(
            f"[ERROR] Could not load embedding model: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    embeddings = embed_texts([record["text"] for record in result.records], model)

    try:
        store = VectorStore(args.persist_directory)
        written = store.upsert_chunks(result.records, embeddings)
        indexed_vectors = store.count()
    except Exception as exc:
        print(f"[ERROR] ChromaDB indexing failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("\n=== Indexing summary ===")
    print(f"PDFs found: {len(pdf_paths)}")
    print(f"PDFs processed successfully: {len(pdf_paths) - len(failed_pdfs)}")
    print(f"Pages extracted: {len(page_records)}")
    print(f"Chunks after Spark filtering: {result.chunk_count}")
    print(f"Vectors written in this run: {written}")
    print(f"Indexed vectors in ChromaDB: {indexed_vectors}")
    print(f"Collection stored at: {args.persist_directory}")

    if empty_pages:
        print(
            f"WARNING: {empty_pages} page(s) had no extractable text "
            "(scanned PDFs need OCR, which is not implemented).",
            file=sys.stderr,
        )
    if failed_pdfs:
        print(
            "[ERROR] Failed PDFs: " + ", ".join(failed_pdfs),
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
