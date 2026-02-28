"""Pinecone vector-database helpers."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pinecone import Index


class EmbeddingModel(str, Enum):
    """Supported OpenAI embedding models."""

    SMALL = "text-embedding-3-small"
    LARGE = "text-embedding-3-large"


def get_index(
    index_name: str,
    api_key: str,
    embedding_model: EmbeddingModel | str = EmbeddingModel.SMALL,
) -> Index:
    """Connect to (or create) a Pinecone index sized for the chosen embedding model.

    Parameters
    ----------
    index_name:
        Name of the Pinecone index.
    api_key:
        Pinecone API key.
    embedding_model:
        Which OpenAI embedding to use.  Accepts an ``EmbeddingModel`` enum
        value or one of the raw strings ``"text-embedding-3-small"`` /
        ``"text-embedding-3-large"``.  The dimension of the index is set
        automatically (1536 for small, 3072 for large).

    Returns
    -------
    pinecone.Index
        A ready-to-use Pinecone index handle.
    """
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError as exc:
        raise RuntimeError(
            "pinecone is required. Install with: pip install pinecone"
        ) from exc

    embedding_model = EmbeddingModel(embedding_model)
    dimension = 1536 if embedding_model == EmbeddingModel.SMALL else 3072

    pc = Pinecone(api_key=api_key)

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    return pc.Index(index_name)
