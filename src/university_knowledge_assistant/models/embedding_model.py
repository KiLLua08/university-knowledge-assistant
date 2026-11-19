"""Pretrained sentence embeddings used for both indexing and querying.

The model is loaded explicitly once by the calling script and then passed to
``embed_texts``. It is never fine-tuned in this project. CPU is the default
device because LM Studio may already be using the GPU's VRAM.
"""

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DEVICE = "cpu"


def load_embedding_model(
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE,
) -> SentenceTransformer:
    """Load a pretrained Sentence Transformers model.

    Args:
        model_name: Hugging Face model identifier.
        device: ``"cpu"``, ``"cuda"`` or another torch-compatible device.

    Returns:
        A ready-to-use model instance. Load this once per process, not once
        per text.
    """
    if not model_name.strip():
        raise ValueError("model_name must not be empty")
    if not device.strip():
        raise ValueError("device must not be empty")

    return SentenceTransformer(model_name, device=device)


def embed_texts(
    texts: Sequence[str],
    model: SentenceTransformer,
    *,
    batch_size: int = 32,
    normalize_embeddings: bool = True,
) -> list[list[float]]:
    """Encode texts into numerical vectors with an already loaded model.

    Args:
        texts: Texts to encode. An empty sequence returns an empty list.
        model: Model returned by ``load_embedding_model``.
        batch_size: Number of texts encoded at once.
        normalize_embeddings: Unit-normalize vectors so cosine/L2 ranking is
            consistent.

    Returns:
        One list of floats per input text, in the same order.
    """
    if not texts:
        return []
    if any(not isinstance(text, str) for text in texts):
        raise TypeError("all texts must be strings")

    vectors = model.encode(
        list(texts),
        batch_size=batch_size,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=normalize_embeddings,
    )

    return [[float(value) for value in vector] for vector in vectors]
