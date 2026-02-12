"""Knowledge base backed by ChromaDB for vector similarity search.

Documents are loaded from a directory of ``.txt`` and ``.md`` files,
chunked, embedded via OpenAI embeddings, and stored in a local ChromaDB
collection for retrieval at query time.
"""

import hashlib
import os
from pathlib import Path

import chromadb
from openai import OpenAI

# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------

_CHUNK_SIZE = 500  # approximate tokens per chunk (measured in words here)
_CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split *text* into overlapping word-level chunks."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def _stable_id(text: str, index: int) -> str:
    """Deterministic chunk id so re-ingestion is idempotent."""
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    return f"chunk-{digest}-{index}"


# ---------------------------------------------------------------------------
# KnowledgeBase
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """Load documents, embed them, and answer similarity queries.

    Parameters
    ----------
    openai_client:
        An authenticated ``openai.OpenAI`` client instance.
    embedding_model:
        Name of the OpenAI embedding model to use.
    persist_directory:
        Where ChromaDB stores its data on disk.  Set to ``None`` for an
        ephemeral in-memory store (useful in tests / notebooks).
    collection_name:
        ChromaDB collection name.
    """

    def __init__(
        self,
        openai_client: OpenAI,
        embedding_model: str = "text-embedding-3-small",
        persist_directory: str | None = "chroma_db",
        collection_name: str = "knowledge_base",
    ) -> None:
        self._client = openai_client
        self._embedding_model = embedding_model

        if persist_directory:
            self._chroma = chromadb.PersistentClient(path=persist_directory)
        else:
            self._chroma = chromadb.Client()

        self._collection = self._chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a list of texts via the OpenAI API."""
        response = self._client.embeddings.create(
            input=texts,
            model=self._embedding_model,
        )
        return [item.embedding for item in response.data]

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def load_directory(self, directory: str) -> int:
        """Recursively load ``.txt`` and ``.md`` files from *directory*.

        Returns the number of chunks ingested.
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Knowledge base directory not found: {directory}")

        total_chunks = 0
        for filepath in sorted(dir_path.rglob("*")):
            if filepath.suffix.lower() in (".txt", ".md"):
                total_chunks += self.load_file(str(filepath))
        return total_chunks

    def load_file(self, filepath: str) -> int:
        """Load and index a single file. Returns number of chunks added."""
        text = Path(filepath).read_text(encoding="utf-8")
        return self.load_text(text, source=filepath)

    def load_text(self, text: str, source: str = "inline") -> int:
        """Chunk, embed, and store a raw text string. Returns chunk count."""
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        ids = [_stable_id(chunk, i) for i, chunk in enumerate(chunks)]
        embeddings = self._embed(chunks)
        metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def query(self, question: str, n_results: int = 3) -> list[dict]:
        """Return the top *n_results* most relevant chunks for *question*.

        Each result dict contains ``text``, ``source``, and ``distance``.
        """
        query_embedding = self._embed([question])[0]
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        output: list[dict] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "distance": dist,
            })
        return output

    @property
    def document_count(self) -> int:
        """Number of chunks currently stored."""
        return self._collection.count()
