"""Ask one question through the full RAG pipeline from the command line.

Requires an indexed ChromaDB collection and a running LM Studio server with
the configured model loaded.
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

from university_knowledge_assistant.pipelines import RAGPipeline

DEFAULT_QUESTION = "Explain backpropagation using the indexed course material."


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--top-k", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = RAGPipeline().answer(args.question, top_k=args.top_k)
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Question: {result['question']}")
    print(f"\nAnswer:\n{result['answer']}")
    print("\nSources:")
    if not result["sources"]:
        print("  (none)")
    for source in result["sources"]:
        print(
            f"  - {source['filename']}, page {source['page_number']} "
            f"(chunk={source['chunk_id']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
