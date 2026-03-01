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


def query_chunks(
    index: Index,
    prompt: str,
    model: EmbeddingModel | str = EmbeddingModel.SMALL,
    namespace: str = "",
    top_k: int = 3,
    include_metadata: bool = True,
) -> list[dict]:
    """Embed a prompt and return the closest matching chunks from Pinecone.

    Parameters
    ----------
    index:
        A Pinecone index handle (from ``get_index``).
    prompt:
        The user's question to embed and search for.
    model:
        OpenAI embedding model to use.
    namespace:
        Pinecone namespace to query.
    top_k:
        Number of results to return.
    include_metadata:
        Whether to include stored metadata in results.

    Returns
    -------
    list[dict]
        Each dict has ``text``, ``score``, and ``id``.
        If *include_metadata* is True, the full ``metadata`` dict is also included.
    """
    from openai import OpenAI

    client = OpenAI()
    embedding = client.embeddings.create(
        input=prompt,
        model=EmbeddingModel(model).value,
    )
    vector = embedding.data[0].embedding

    results = index.query(
        vector=vector,
        top_k=top_k,
        namespace=namespace,
        include_metadata=include_metadata,
    )

    chunks = []
    for match in results.matches:
        entry = {
            "id": match.id,
            "score": match.score,
            "text": match.metadata.get("text", "") if match.metadata else "",
        }
        if include_metadata and match.metadata:
            entry["metadata"] = match.metadata
        chunks.append(entry)

    return chunks
