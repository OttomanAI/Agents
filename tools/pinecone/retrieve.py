#!/usr/bin/env python3
"""Retrieve context from Pinecone for downstream agent prompts.

Examples:
  python tools/pinecone/retrieve.py \
    --index my-index \
    --namespace sales-kb \
    --query-text "renewal follow-up" \
    --top-k 5

  python tools/pinecone/retrieve.py \
    --index my-index \
    --namespace sales-kb \
    --vector-json "[0.1, 0.2, 0.3]" \
    --top-k 3 \
    --output json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any


DEFAULT_TEXT_FALLBACK_KEYS = ("text", "chunk_text", "content", "body")


@dataclass(frozen=True)
class RetrievalMatch:
    """Normalized match payload from Pinecone query results."""

    match_id: str
    score: float | None
    metadata: dict[str, Any]
    text: str


def _load_pinecone_client(api_key: str):
    try:
        from pinecone import Pinecone
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "pinecone package is required. Install with: pip install pinecone"
        ) from exc
    return Pinecone(api_key=api_key)


def _build_index(client: Any, index_name: str, host: str | None):
    if host:
        try:
            return client.Index(host=host)
        except TypeError:
            return client.Index(name=index_name, host=host)

    try:
        return client.Index(index_name)
    except TypeError:
        return client.Index(name=index_name)


def _embed_query_text(query_text: str, model: str, openai_api_key: str | None) -> list[float]:
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required when using --query-text. "
            "Set it in the environment or pass --openai-api-key."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "openai package is required for --query-text. Install with: pip install openai"
        ) from exc

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model, input=query_text)
    return list(response.data[0].embedding)


def _parse_vector(vector_json: str) -> list[float]:
    try:
        parsed = json.loads(vector_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --vector-json value: {exc}") from exc

    if not isinstance(parsed, list) or not parsed:
        raise ValueError("--vector-json must be a non-empty JSON array of numbers")

    vector: list[float] = []
    for value in parsed:
        if not isinstance(value, (int, float)):
            raise ValueError("--vector-json must contain only numbers")
        vector.append(float(value))

    return vector


def _parse_filter(filter_json: str | None) -> dict[str, Any] | None:
    if not filter_json:
        return None

    try:
        parsed = json.loads(filter_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --filter-json value: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("--filter-json must be a JSON object")

    return parsed


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        as_dict = value.to_dict()
        if isinstance(as_dict, dict):
            return as_dict
    return {
        "id": getattr(value, "id", ""),
        "score": getattr(value, "score", None),
        "metadata": getattr(value, "metadata", {}) or {},
    }


def _normalize_matches(raw_result: Any, text_key: str) -> list[RetrievalMatch]:
    raw = _to_dict(raw_result)
    raw_matches = raw.get("matches", [])

    normalized: list[RetrievalMatch] = []
    for item in raw_matches:
        match = _to_dict(item)
        metadata = match.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        text = str(metadata.get(text_key, "")).strip()
        if not text:
            for key in DEFAULT_TEXT_FALLBACK_KEYS:
                fallback = str(metadata.get(key, "")).strip()
                if fallback:
                    text = fallback
                    break

        score = match.get("score")
        normalized.append(
            RetrievalMatch(
                match_id=str(match.get("id", "")),
                score=float(score) if isinstance(score, (int, float)) else None,
                metadata=metadata,
                text=text,
            )
        )

    return normalized


def _query_pinecone(
    *,
    api_key: str,
    index_name: str,
    namespace: str,
    host: str | None,
    top_k: int,
    vector: list[float] | None,
    query_id: str | None,
    filter_payload: dict[str, Any] | None,
    text_key: str,
) -> list[RetrievalMatch]:
    client = _load_pinecone_client(api_key=api_key)
    index = _build_index(client=client, index_name=index_name, host=host)

    query_kwargs: dict[str, Any] = {
        "top_k": top_k,
        "namespace": namespace,
        "include_metadata": True,
    }
    if vector is not None:
        query_kwargs["vector"] = vector
    if query_id:
        query_kwargs["id"] = query_id
    if filter_payload:
        query_kwargs["filter"] = filter_payload

    result = index.query(**query_kwargs)
    return _normalize_matches(result, text_key=text_key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retrieve data from Pinecone")
    parser.add_argument("--api-key", default=os.getenv("PINECONE_API_KEY"), help="Pinecone API key")
    parser.add_argument("--index", required=True, help="Pinecone index name")
    parser.add_argument("--namespace", default="", help="Pinecone namespace")
    parser.add_argument("--host", help="Optional index host (recommended for serverless indexes)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of matches to return")
    parser.add_argument("--filter-json", help="Optional metadata filter as JSON object")
    parser.add_argument(
        "--text-key",
        default="text",
        help="Metadata key used when rendering text output",
    )
    parser.add_argument("--output", choices=["text", "json"], default="text")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--query-text",
        help="Query text to embed via OpenAI, then search Pinecone",
    )
    source_group.add_argument(
        "--vector-json",
        help="Query vector as a JSON array, for example '[0.1, 0.2, 0.3]'",
    )
    source_group.add_argument("--id", dest="query_id", help="Existing vector ID for ID-based query")

    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        help="OpenAI embedding model used with --query-text",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (required with --query-text if OPENAI_API_KEY is not set)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.api_key:
        raise RuntimeError(
            "PINECONE_API_KEY is required. Set it in the environment or pass --api-key."
        )
    if args.top_k < 1:
        raise ValueError("--top-k must be >= 1")

    filter_payload = _parse_filter(args.filter_json)

    vector: list[float] | None = None
    if args.query_text:
        vector = _embed_query_text(
            query_text=args.query_text,
            model=args.embedding_model,
            openai_api_key=args.openai_api_key,
        )
    elif args.vector_json:
        vector = _parse_vector(args.vector_json)

    matches = _query_pinecone(
        api_key=args.api_key,
        index_name=args.index,
        namespace=args.namespace,
        host=args.host,
        top_k=args.top_k,
        vector=vector,
        query_id=args.query_id,
        filter_payload=filter_payload,
        text_key=args.text_key,
    )

    if args.output == "json":
        payload = [
            {
                "id": match.match_id,
                "score": match.score,
                "metadata": match.metadata,
                "text": match.text,
            }
            for match in matches
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0

    text_chunks = [match.text for match in matches if match.text]
    print("\n\n".join(text_chunks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
