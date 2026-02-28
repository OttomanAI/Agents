# File Breakdown Report

**Project:** TurboAutomations (Agents)
**Generated:** 2026-02-28
**Total Files:** 17 | **Total Lines:** 1,176 | **Packages:** 3

---

## Directory Tree

```
Agents/                          (root)
├── .gitignore                   15 lines
├── LICENSE                      21 lines
├── README.md                    14 lines
├── pyproject.toml               20 lines
│
├── Agents/                      (core AI agent package)
│   ├── __init__.py              20 lines
│   ├── cli.py                   117 lines
│   ├── config.py                140 lines
│   ├── helpers.py               21 lines
│   ├── knowledge_base.py        157 lines
│   └── rag_agent.py             90 lines
│
├── CommsIO/                     (communications I/O package)
│   ├── __init__.py              26 lines
│   ├── gmail.py                 189 lines
│   └── telegram.py              178 lines
│
└── workflows/                   (workflow templates)
    ├── __init__.py              1 line
    └── KastroAI/
        ├── __init__.py          3 lines
        └── CreateKnowledgeBase.ipynb  155 lines
```

---

## Files by Extension

| Extension | Count | Description          |
|-----------|------:|----------------------|
| `.py`     |    11 | Python source files  |
| `.toml`   |     1 | Project config       |
| `.md`     |     1 | Documentation        |
| `.ipynb`  |     1 | Jupyter notebook     |
| (other)   |     2 | .gitignore, LICENSE  |

---

## Files by Size (lines, descending)

| File                                       | Lines | % of Total |
|--------------------------------------------|------:|-----------:|
| `CommsIO/gmail.py`                         |   189 |     16.1%  |
| `CommsIO/telegram.py`                      |   178 |     15.1%  |
| `Agents/knowledge_base.py`                 |   157 |     13.4%  |
| `workflows/KastroAI/CreateKnowledgeBase.ipynb` | 155 |     13.2%  |
| `Agents/config.py`                         |   140 |     11.9%  |
| `Agents/cli.py`                            |   117 |      9.9%  |
| `Agents/rag_agent.py`                      |    90 |      7.7%  |
| `CommsIO/__init__.py`                      |    26 |      2.2%  |
| `LICENSE`                                  |    21 |      1.8%  |
| `Agents/helpers.py`                        |    21 |      1.8%  |
| `pyproject.toml`                           |    20 |      1.7%  |
| `Agents/__init__.py`                       |    20 |      1.7%  |
| `.gitignore`                               |    15 |      1.3%  |
| `README.md`                                |    14 |      1.2%  |
| `workflows/KastroAI/__init__.py`           |     3 |      0.3%  |
| `workflows/__init__.py`                    |     1 |      0.1%  |

---

## Package Breakdown

### `Agents/` — Core AI Agent (545 lines)

| File                | Lines | Purpose |
|---------------------|------:|---------|
| `knowledge_base.py` |   157 | ChromaDB-backed vector store; loads `.txt`/`.md` files, chunks text, runs similarity search via OpenAI embeddings |
| `config.py`         |   140 | Unified config from defaults -> YAML -> environment variables; supports `.env` files; masks API keys in repr |
| `cli.py`            |   117 | CLI entry point (argparse); interactive and single-question modes; configurable logging |
| `rag_agent.py`      |    90 | RAG conversational agent; retrieves context chunks, calls OpenAI chat completions, maintains 10-message history |
| `helpers.py`        |    21 | Text chunking utility with configurable chunk size and overlap |
| `__init__.py`       |    20 | Lazy-loads `Config`, `KnowledgeBase`, `RAGAgent`, `chunk_text_for_kb` |

### `CommsIO/` — Communications I/O (393 lines)

| File            | Lines | Purpose |
|-----------------|------:|---------|
| `gmail.py`      |   189 | Gmail inbox watcher using OAuth2; polls for new emails; extracts headers, body, and metadata as JSON |
| `telegram.py`   |   178 | Telegram bot API wrapper; message polling, sending, typing indicators; normalizes updates to JSON |
| `__init__.py`   |    26 | Exports `GmailInbox` and `TelegramBot` classes |

### `workflows/` — Workflow Templates (159 lines)

| File                                | Lines | Purpose |
|-------------------------------------|------:|---------|
| `KastroAI/CreateKnowledgeBase.ipynb`|   155 | Example notebook: Telegram message retrieval + JMESPath extraction for knowledge base creation |
| `KastroAI/__init__.py`             |     3 | Subpackage init |
| `__init__.py`                       |     1 | Package init |

---

## Lines of Code by Package

```
Agents/    ██████████████████████████████████  545  (46.3%)
CommsIO/   █████████████████████████          393  (33.4%)
workflows/ ██████████                         159  (13.5%)
(root)      █████                              79  ( 6.7%)
```

---

## Key Dependencies (from `pyproject.toml`)

| Dependency       | Version   | Used By |
|------------------|-----------|---------|
| `openai`         | >=1.0.0   | `rag_agent.py`, `knowledge_base.py` — LLM calls and embeddings |
| `chromadb`       | >=0.5.0   | `knowledge_base.py` — vector storage and similarity search |
| `PyYAML`         | >=6.0.0   | `config.py` — YAML config file parsing |
| `python-dotenv`  | >=1.0.0   | `config.py` — `.env` file loading |

**Optional / conditionally imported:**
- `google-api-python-client`, `google-auth-oauthlib` — Gmail integration
- `jmespath` — workflow data extraction
