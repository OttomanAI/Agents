"""Knowledge base backed by ChromaDB for vector similarity search."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import chromadb
from openai import OpenAI

_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += step
    return chunks


def _stable_id(text: str, index: int) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"chunk-{digest}-{index}"


class KnowledgeBase:
    """Load documents, embed them, and answer similarity queries."""

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

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            input=texts,
            model=self._embedding_model,
        )
        return [item.embedding for item in response.data]

    def load_directory(self, directory: str) -> int:
        """Recursively load .txt/.md files from directory."""

        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Knowledge base directory not found: {directory}")

        total_chunks = 0
        for filepath in sorted(dir_path.rglob("*")):
            if ".ipynb_checkpoints" in filepath.parts:
                continue
            if filepath.suffix.lower() in (".txt", ".md"):
                total_chunks += self.load_file(str(filepath))
        return total_chunks

    def load_file(self, filepath: str) -> int:
        text = Path(filepath).read_text(encoding="utf-8")
        return self.load_text(text, source=filepath)

    def load_text(self, text: str, source: str = "inline") -> int:
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

    def query(self, question: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Return top matching chunks for a question."""

        if not question.strip():
            raise ValueError("question must not be empty")
        if n_results <= 0:
            raise ValueError("n_results must be > 0")
        if self.document_count == 0:
            return []

        query_embedding = self._embed([question])[0]
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        output: list[dict[str, Any]] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            metadata = meta or {}
            output.append(
                {
                    "text": doc,
                    "source": metadata.get("source", "unknown"),
                    "distance": dist,
                }
            )
        return output

    @property
    def document_count(self) -> int:
        return self._collection.count()
