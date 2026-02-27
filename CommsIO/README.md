# CommLinkIO

CommLinkIO is organized as a multi-integration Python package with separate domains for Telegram and Gmail.

## Project layout

```text
CommLinkIO/
├── src/commlinkio/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── json_extractor.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── json_extract.py
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   └── bot_client.py
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── actions.py
│   │   │   └── messages.py
│   │   ├── readers/
│   │   │   ├── __init__.py
│   │   │   └── updates.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── send.py
│   │   └── triggers/
│   │       ├── __init__.py
│   │       └── updates_trigger.py
│   └── gmail/
│       ├── __init__.py
│       ├── clients/
│       │   ├── __init__.py
│       │   └── watch_client.py
│       ├── functions/
│       │   └── __init__.py
│       └── triggers/
│           ├── __init__.py
│           └── inbox_watch_trigger.py
├── scripts/
│   ├── run_json_extract.py
│   ├── run_telegram_send.py
│   ├── run_telegram_updates_trigger.py
│   └── run_gmail_inbox_watch_trigger.py
├── tests/
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

## Run Telegram updates trigger

Requires `TELEGRAM_BOT_TOKEN` in your environment or `.env` file.

```bash
commlinkio-telegram-updates-trigger
```

Or:

```bash
python -m commlinkio.telegram.triggers.updates_trigger
```

## Send Telegram typing/message actions

Requires `TELEGRAM_BOT_TOKEN` in your environment or `.env` file (or pass `--token` on each command).

Send typing action:

```bash
commlinkio-telegram-send typing --chat-id 123456789
```

Send message:

```bash
commlinkio-telegram-send message --chat-id 123456789 --text "Hello from CommLinkIO"
```

Optional parse mode:

```bash
commlinkio-telegram-send message --chat-id @my_channel --text "<b>Hello</b>" --parse-mode HTML
```

## Run Gmail inbox watch trigger (scaffold)

```bash
commlinkio-gmail-inbox-watch-trigger
```

The Gmail side is scaffolded for now and ready for Google API credentials/watch topic integration.

## Generic JSON extraction tool

Use this for Telegram payloads, Gmail payloads, or any other JSON file.

```bash
commlinkio-json-extract path/to/file.json -q "message.text"
```

Multiple queries:

```bash
commlinkio-json-extract path/to/file.json \
  -q "updates[*].id" \
  -q "['meta.data'].owner.id"
```

Return one value per query:

```bash
commlinkio-json-extract path/to/file.json -q "updates[-1].id" --first
```

Fail if required fields are missing:

```bash
commlinkio-json-extract path/to/file.json -q "message.chat.id" --required
```
