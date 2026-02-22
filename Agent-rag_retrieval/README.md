# RAG Retrieval AI Agent

A retrieval-augmented generation (RAG) agent that uses OpenAI and a local vector store (ChromaDB) to answer questions grounded in a custom knowledge base.

## Project Structure

```
├── agent/
│   ├── __init__.py
│   ├── cli.py             # Production CLI entrypoint
│   ├── config.py          # Config loader (env vars + YAML)
│   ├── knowledge_base.py  # Document ingestion & vector search
│   └── rag_agent.py       # RAG agent with system message
├── knowledge_base/
│   └── documents/         # Drop .txt and .md files here
├── notebooks/
│   └── rag_agent_demo.ipynb  # Jupyter notebook for manual testing
├── main.py                # Backward-compatible CLI shim
├── tests/
│   ├── test_config.py
│   └── test_rag_agent.py
├── requirements.txt
├── .env.example
└── config.yaml.example
```

## Configuration

API keys and settings can be provided in **two ways** (both are supported simultaneously):

| Method | File | Priority |
|---|---|---|
| Environment variables | `.env` | Highest |
| YAML config file | `config.yaml` | Lower |

Environment variables always override values from `config.yaml`.

### Option 1: Environment Variables

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### Option 2: YAML Config File

```bash
cp config.yaml.example config.yaml
# Edit config.yaml and set your openai_api_key
```

### Available Settings

| Env Var | YAML Key | Default |
|---|---|---|
| `OPENAI_API_KEY` | `openai_api_key` | *(required)* |
| `OPENAI_MODEL` | `openai_model` | `gpt-4o` |
| `EMBEDDING_MODEL` | `embedding_model` | `text-embedding-3-small` |
| `KNOWLEDGE_BASE_PATH` | `knowledge_base_path` | `knowledge_base/documents` |
| `SYSTEM_MESSAGE` | `system_message` | *(built-in default)* |

## Running Locally

```bash
pip install -r requirements.txt

# Interactive CLI
python -m agent.cli

# Or (legacy shim)
python main.py

# Use only env vars (ignore config.yaml)
python -m agent.cli --env-only

# Use a specific config file
python -m agent.cli --config path/to/config.yaml

# One-shot question (non-interactive)
python -m agent.cli --question "What is your return policy?"
```

## Containerization

This repo is intentionally not dockerized. Containerization is handled by the parent repository that composes this module with other services.

## Jupyter Notebook

The notebook at `notebooks/rag_agent_demo.ipynb` walks through every component:

1. **Config** - load and validate settings
2. **Knowledge Base** - ingest documents, add custom text, run similarity search
3. **RAG Agent** - ask questions, multi-turn conversation, custom system messages

## Adding Knowledge Base Documents

Drop `.txt` or `.md` files into `knowledge_base/documents/`. They are automatically chunked, embedded, and indexed when the agent starts.

## Running Tests

```bash
python -m unittest discover -s tests -v
```
