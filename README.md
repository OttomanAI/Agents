# Agent Starter

Agent Starter is a professional Python baseline for building task-focused agents with a clean package layout, command-line tools, and test coverage.

## Project layout

```text
New project/
├── src/agent/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── run.py
│   └── triggers/
│       ├── __init__.py
│       └── heartbeat.py
├── scripts/
│   ├── run_agent.py
│   └── run_heartbeat.py
├── tests/
│   ├── test_cli.py
│   └── test_engine.py
├── AGENTS.md
├── pyproject.toml
├── requirements.txt
└── LICENSE
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the agent CLI

```bash
agent-run \
  --content "Draft a concise daily status update" \
  --system-message "Respond in a professional and direct tone." \
  --knowledge-base "Daily report should include blockers, owners, and ETAs."
```

Or run the module directly:

```bash
python -m agent.tools.run \
  --content "Draft a concise daily status update" \
  --system-message "Respond in a professional and direct tone." \
  --knowledge-base "Daily report should include blockers, owners, and ETAs."
```

## Run the heartbeat trigger

```bash
agent-heartbeat --interval 5 --count 3
```

## Retrieve context from Pinecone

Use the standalone retriever tool to fetch context and pipe it into the agent.

```bash
python tools/pinecone/retrieve.py \
  --index your-index \
  --namespace your-kb \
  --query-text "Draft a renewal follow-up email" \
  --top-k 5
```

Use vector input directly:

```bash
python tools/pinecone/retrieve.py \
  --index your-index \
  --namespace your-kb \
  --vector-json "[0.1, 0.2, 0.3]" \
  --top-k 3 \
  --output json
```

If your index does not use the default metadata field, pass `--text-key` (for example `chunk_text`).

## Run tests

```bash
pytest
```

## Development notes

- Keep business logic in `src/agent/core`.
- Keep input/output adapters in `src/agent/tools` and `src/agent/triggers`.
- Add or update tests for every behavioral change.
