"""Query the existing ChromaDB collection with a sample deep-learning question.

Run from the repository root with ``python scripts/test_retrieval.py`` after
``python scripts/index_documents.py`` has created the collection.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from university_knowledge_assistant.models import (
    DEFAULT_DEVICE,
    DEFAULT_MODEL_NAME,
    embed_texts,
    load_embedding_model,
)
from university_knowledge_assistant.retrieval import VectorStore

DEFAULT_PERSIST_DIR = REPO_ROOT / "data" / "chroma"
DEFAULT_QUESTION = "What is deep learning and how does a neural network learn?"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persist-directory", type=Path, default=DEFAULT_PERSIST_DIR)
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.top_k <= 0:
        print("[ERROR] --top-k must be positive", file=sys.stderr)
        return 1
    if not args.persist_directory.exists():
        print(
            f"[ERROR] No collection found at {args.persist_directory}. "
            "Run scripts/index_documents.py first.",
            file=sys.stderr,
        )
        return 1

    try:
        store = VectorStore(args.persist_directory)
    except Exception as exc:
        print(
            f"[ERROR] Could not open ChromaDB collection: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    if store.count() == 0:
        print(
            "[ERROR] The collection is empty. Run scripts/index_documents.py first.",
            file=sys.stderr,
        )
        return 1

    print(f"Loading embedding model '{args.model_name}' on {args.device}...", flush=True)
    try:
        model = load_embedding_model(args.model_name, args.device)
    except Exception as exc:
        print(
            f"[ERROR] Could not load embedding model: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    # The same model that produced the stored vectors now encodes the query.
    query_embedding = embed_texts([args.question], model)[0]
    results = store.search(query_embedding, top_k=args.top_k)

    print(f"\nQuestion: {args.question}")
    print(f"Retrieved {len(results)} chunk(s):")

    for position, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print(f"\n--- Result {position} (distance={result['distance']:.4f}) ---")
        print(f"File: {metadata.get('filename')}")
        print(f"Page: {metadata.get('page_number')}")
        print(f"Document ID: {metadata.get('document_id')}")
        print(f"Chunk ID: {metadata.get('chunk_id')}")
        print(f"Text:\n{result['text']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
