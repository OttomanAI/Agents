"""Importable agents package."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["Config", "KnowledgeBase", "RAGAgent", "chunk_text_for_kb"]


def __getattr__(name: str) -> Any:
    if name == "Config":
        return import_module("Agents.config").Config
    if name == "KnowledgeBase":
        return import_module("Agents.knowledge_base").KnowledgeBase
    if name == "RAGAgent":
        return import_module("Agents.rag_agent").RAGAgent
    if name == "chunk_text_for_kb":
        return import_module("Agents.helpers").chunk_text_for_kb
    raise AttributeError(f"module 'Agents' has no attribute {name!r}")
