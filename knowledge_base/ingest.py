"""Ingest structured ``.kb`` documents into Pinecone for RAG retrieval.

Reads every ``.kb`` file in ``knowledge_base/documents/``, parses the
pre-chunked entries (KB_ID, TYPE, TITLE, TAGS, SOURCE, VERSION, PARENT_ID,
TEXT), embeds each chunk with OpenAI ``text-embedding-3-small``, and upserts
into the ``faqs`` namespace.

Run as a standalone script::

    python -m knowledge_base.ingest
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import openai
from pinecone import Pinecone

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "jaded-rose")
NS_FAQS: str = "faqs"

DOCUMENTS_DIR = Path(__file__).parent / "documents"

# ---------------------------------------------------------------------------
# Structured .kb parser
# ---------------------------------------------------------------------------

_CHUNK_DELIMITER = "--- KB_CHUNK_END ---"


def _parse_kb_file(text: str) -> List[Dict[str, str]]:
    """Parse a structured ``.kb`` file into a list of chunk dicts.

    Each chunk dict contains keys: kb_id, type, title, tags, source, version,
    parent_id, text.
    """
    raw_chunks = text.split(_CHUNK_DELIMITER)
    parsed: List[Dict[str, str]] = []

    for raw in raw_chunks:
        raw = raw.strip()
        if not raw:
            continue

        chunk: Dict[str, str] = {}
        # Extract header fields (KEY: value)
        field_pattern = re.compile(
            r"^(KB_ID|TYPE|TITLE|TAGS|SOURCE|VERSION|PARENT_ID):\s*(.+)$",
            re.MULTILINE,
        )
        for match in field_pattern.finditer(raw):
            key = match.group(1).lower()
            chunk[key] = match.group(2).strip()

        # Extract TEXT: block — everything after "TEXT:\n"
        text_match = re.search(r"^TEXT:\s*\n(.*)", raw, re.DOTALL | re.MULTILINE)
        if text_match:
            chunk["text"] = text_match.group(1).strip()

        # Only include if we have at least kb_id and text
        if chunk.get("kb_id") and chunk.get("text"):
            parsed.append(chunk)

    return parsed


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def _embed_batch(client: openai.OpenAI, texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts with OpenAI.

    Args:
        client: An OpenAI client.
        texts: A list of strings to embed.

    Returns:
        A list of embedding vectors.
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------


def _kb_vector_id(kb_id: str) -> str:
    """Generate a deterministic vector ID from a structured KB_ID.

    Uses the KB_ID directly (truncated hash) so the same KB_ID always maps to
    the same vector — enabling **upsert-overwrites** on re-ingestion.
    """
    return hashlib.sha256(kb_id.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------


def _prepare_vectors(
    client: openai.OpenAI, filepath: Path
) -> List[Tuple[str, List[float], Dict[str, Any]]]:
    """Prepare vectors from a structured .kb file."""
    text = filepath.read_text(encoding="utf-8")
    chunks = _parse_kb_file(text)
    logger.info("📄 %s — %d chunks", filepath.name, len(chunks))

    if not chunks:
        return []

    # Embed: prepend title + tags to text for richer embeddings
    embed_texts = []
    for c in chunks:
        title = c.get("title", "")
        tags = c.get("tags", "")
        body = c.get("text", "")
        embed_texts.append(f"{title}. {tags}. {body}")

    embeddings = _embed_batch(client, embed_texts)

    vectors: List[Tuple[str, List[float], Dict[str, Any]]] = []
    for chunk, embedding in zip(chunks, embeddings):
        vec_id = _kb_vector_id(chunk["kb_id"])
        metadata: Dict[str, Any] = {
            "text": chunk["text"],
            "kb_id": chunk["kb_id"],
            "type": chunk.get("type", ""),
            "title": chunk.get("title", ""),
            "tags": chunk.get("tags", ""),
            "source": chunk.get("source", filepath.name),
            "version": chunk.get("version", ""),
            "parent_id": chunk.get("parent_id", "none"),
        }
        vectors.append((vec_id, embedding, metadata))

    return vectors


def ingest() -> None:
    """Run the full ingestion pipeline: read .kb → embed → upsert."""
    if not OPENAI_API_KEY or not PINECONE_API_KEY:
        logger.error("OPENAI_API_KEY and PINECONE_API_KEY must be set.")
        sys.exit(1)

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)

    kb_files = sorted(DOCUMENTS_DIR.glob("*.kb"))
    if not kb_files:
        logger.warning("No .kb files found in %s", DOCUMENTS_DIR)
        return

    all_vectors: List[Tuple[str, List[float], Dict[str, Any]]] = []

    for filepath in kb_files:
        all_vectors.extend(_prepare_vectors(client, filepath))

    if not all_vectors:
        logger.warning("No chunks parsed from .kb files in %s", DOCUMENTS_DIR)
        return

    # Upsert in batches of 100
    # Pinecone upsert is idempotent — same vector ID overwrites the old record.
    batch_size = 100
    for i in range(0, len(all_vectors), batch_size):
        batch = all_vectors[i : i + batch_size]
        vectors = [
            {"id": vid, "values": emb, "metadata": meta}
            for vid, emb, meta in batch
        ]
        index.upsert(vectors=vectors, namespace=NS_FAQS)
        logger.info("Upserted batch %d–%d", i, i + len(batch))

    logger.info(
        "✅ Ingestion complete — %d vectors upserted to '%s'",
        len(all_vectors),
        NS_FAQS,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ingest()
