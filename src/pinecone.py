"""Helpers for sending chunked knowledge-base text to Pinecone."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_CHUNK_SEPARATOR = "----KB CHUNK----"
EMBEDDING_MODELS = {
    "small": "text-embedding-3-small",
    "large": "text-embedding-3-large",
}


@dataclass(frozen=True)
class PineconeUpsertResult:
    """Normalized summary from a chunked Pinecone upload run."""

    namespace: str
    embedding_model: str
    chunk_count: int
    deleted_existing: bool
    upserted_count: int


def upload_chunked_data_to_pinecone(
    chunked_data: str,
    *,
    index_host: str,
    namespace: str = "",
    embedding_size: str = "small",
    replace_existing: bool = False,
    chunk_separator: str = DEFAULT_CHUNK_SEPARATOR,
    source_name: str = "knowledge_base",
    pinecone_api_key: str | None = None,
    openai_api_key: str | None = None,
    batch_size: int = 100,
) -> PineconeUpsertResult:
    """Send chunked string data to Pinecone using OpenAI embeddings."""
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")

    pinecone_key = _resolve_api_key(
        direct_value=pinecone_api_key,
        env_var="PINECONE_API_KEY",
        error_message="PINECONE_API_KEY is required.",
    )
    openai_key = _resolve_api_key(
        direct_value=openai_api_key,
        env_var="OPENAI_API_KEY",
        error_message="OPENAI_API_KEY is required.",
    )
    model = _resolve_embedding_model(embedding_size)
    host = _normalize_index_host(index_host)
    chunks = _split_chunks(chunked_data, chunk_separator)

    embeddings = _embed_chunks(chunks=chunks, model=model, openai_api_key=openai_key)
    vectors = _build_vectors(chunks=chunks, embeddings=embeddings, source_name=source_name)

    if replace_existing:
        _delete_all_vectors(index_host=host, namespace=namespace, pinecone_api_key=pinecone_key)

    upserted_count = _upsert_vectors(
        index_host=host,
        namespace=namespace,
        vectors=vectors,
        pinecone_api_key=pinecone_key,
        batch_size=batch_size,
    )
    return PineconeUpsertResult(
        namespace=namespace,
        embedding_model=model,
        chunk_count=len(chunks),
        deleted_existing=replace_existing,
        upserted_count=upserted_count,
    )


def _resolve_api_key(*, direct_value: str | None, env_var: str, error_message: str) -> str:
    value = (direct_value or os.getenv(env_var, "")).strip()
    if not value:
        raise ValueError(error_message)
    return value


def _resolve_embedding_model(embedding_size: str) -> str:
    normalized = embedding_size.strip().lower()
    if normalized not in EMBEDDING_MODELS:
        allowed = ", ".join(sorted(EMBEDDING_MODELS))
        raise ValueError(f"embedding_size must be one of: {allowed}")
    return EMBEDDING_MODELS[normalized]


def _normalize_index_host(index_host: str) -> str:
    cleaned = index_host.strip()
    if not cleaned:
        raise ValueError("index_host must be a non-empty string")
    if not cleaned.startswith(("https://", "http://")):
        cleaned = f"https://{cleaned}"
    return cleaned.rstrip("/")


def _split_chunks(chunked_data: str, chunk_separator: str) -> list[str]:
    if not isinstance(chunked_data, str) or not chunked_data.strip():
        raise ValueError("chunked_data must be a non-empty string")

    separator = chunk_separator.strip()
    if not separator:
        raise ValueError("chunk_separator must be a non-empty string")

    chunks = [part.strip() for part in chunked_data.split(separator)]
    filtered = [chunk for chunk in chunks if chunk]
    if not filtered:
        raise ValueError("No chunks found in chunked_data")
    return filtered


def _embed_chunks(*, chunks: list[str], model: str, openai_api_key: str) -> list[list[float]]:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "openai package is required. Install with: pip install openai"
        ) from exc

    client = OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(model=model, input=chunks)
    sorted_rows = sorted(response.data, key=lambda row: row.index)
    return [list(row.embedding) for row in sorted_rows]


def _build_vectors(
    *, chunks: list[str], embeddings: list[list[float]], source_name: str
) -> list[dict[str, Any]]:
    if len(chunks) != len(embeddings):
        raise RuntimeError("Embedding count does not match chunk count")

    vectors: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        values = embeddings[index]
        vector_id = _build_vector_id(source_name=source_name, index=index, chunk=chunk)
        vectors.append(
            {
                "id": vector_id,
                "values": values,
                "metadata": {
                    "text": chunk,
                    "chunk_index": index,
                    "source": source_name,
                },
            }
        )
    return vectors


def _build_vector_id(*, source_name: str, index: int, chunk: str) -> str:
    digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:16]
    safe_source = source_name.strip() or "knowledge_base"
    return f"{safe_source}-{index}-{digest}"


def _delete_all_vectors(*, index_host: str, namespace: str, pinecone_api_key: str) -> None:
    _post_json(
        url=f"{index_host}/vectors/delete",
        payload={"namespace": namespace, "deleteAll": True},
        pinecone_api_key=pinecone_api_key,
    )


def _upsert_vectors(
    *,
    index_host: str,
    namespace: str,
    vectors: list[dict[str, Any]],
    pinecone_api_key: str,
    batch_size: int,
) -> int:
    total = 0
    for offset in range(0, len(vectors), batch_size):
        batch = vectors[offset : offset + batch_size]
        result = _post_json(
            url=f"{index_host}/vectors/upsert",
            payload={"namespace": namespace, "vectors": batch},
            pinecone_api_key=pinecone_api_key,
        )
        upserted = result.get("upsertedCount")
        if isinstance(upserted, int):
            total += upserted
        else:
            total += len(batch)
    return total


def _post_json(*, url: str, payload: dict[str, Any], pinecone_api_key: str) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Api-Key": pinecone_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Pinecone request failed ({url}): {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Pinecone request failed ({url}): {exc.reason}") from exc

    if not raw.strip():
        return {}
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, dict):
        return {}
    return decoded
