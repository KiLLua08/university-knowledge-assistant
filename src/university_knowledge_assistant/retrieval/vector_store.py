"""Persistent ChromaDB storage and vector similarity search.

The store receives vectors from the caller instead of embedding text itself.
The indexing and retrieval scripts therefore share one Sentence Transformers
model, which guarantees that stored and query vectors live in the same space.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import chromadb

DEFAULT_COLLECTION_NAME = "university_documents"
DEFAULT_PERSIST_DIRECTORY = "data/chroma"


class VectorStore:
    """Thin wrapper around a persistent local ChromaDB collection."""

    def __init__(
        self,
        persist_directory: str | Path = DEFAULT_PERSIST_DIRECTORY,
        *,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(self.persist_directory))
        # We always provide explicit embeddings, so ChromaDB must not create
        # or download its own default embedding model.
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
        )

    def count(self) -> int:
        """Number of vectors currently stored in the collection."""
        return self._collection.count()

    def upsert_chunks(
        self,
        chunks: Sequence[dict[str, Any]],
        embeddings: Sequence[Sequence[float]],
    ) -> int:
        """Insert or update chunks with their embeddings.

        Upsert uses the deterministic ``chunk_id`` as the ChromaDB ID, so
        indexing the same PDF twice does not create duplicate vectors.

        Returns:
            Number of chunk records written in this call.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        vectors: list[list[float]] = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = str(chunk["chunk_id"])
            metadata: dict[str, Any] = {
                "document_id": str(chunk["document_id"]),
                "filename": str(chunk["filename"]),
                "page_number": int(chunk["page_number"]),
                "chunk_id": chunk_id,
            }
            if "chunk_index" in chunk:
                metadata["chunk_index"] = int(chunk["chunk_index"])

            ids.append(chunk_id)
            documents.append(str(chunk["text"]))
            metadatas.append(metadata)
            vectors.append([float(value) for value in embedding])

        self._collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def search(
        self, query_embedding: Sequence[float], *, top_k: int = 3
    ) -> list[dict[str, Any]]:
        """Return the ``top_k`` most similar chunks for a query vector.

        Args:
            query_embedding: Vector produced by the same embedding model used
                for indexing.
            top_k: Maximum number of results to return.

        Returns:
            Lists of dictionaries containing ``id``, ``text``, ``metadata``
            and ChromaDB ``distance`` (smaller means more similar).
        """
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")

        total = self.count()
        if total == 0:
            return []

        result = self._collection.query(
            query_embeddings=[[float(value) for value in query_embedding]],
            n_results=min(top_k, total),
            include=["documents", "metadatas", "distances"],
        )

        ids = result["ids"][0] if result["ids"] else []
        documents = result["documents"][0] if result["documents"] else []
        metadatas = result["metadatas"][0] if result["metadatas"] else []
        distances = result["distances"][0] if result["distances"] else []

        return [
            {
                "id": chunk_id,
                "text": text,
                "metadata": metadata,
                "distance": distance,
            }
            for chunk_id, text, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]
