# ContextGuard Local MVP

ContextGuard Local MVP is a local prototype for detecting risky paste/upload behavior and making context-aware `PASS`, `WARN`, or `BLOCK` decisions with a local AI risk engine.

Primary planning documents:

- `MVP.md`: MVP scope and demo scenarios
- `MVP_DEVELOPMENT_PLAN.md`: implementation order, test requirements, and completion criteria
- `IMPLEMENTATION.md`: original broader TraceForge implementation spec

## Development Rule

Every feature must include tests. Before implementing a phase, check `MVP_DEVELOPMENT_PLAN.md` and create or update the required test cases.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Test

```bash
pytest
```

## Run Local Agent API

```bash
uvicorn agent.app.main:app --reload --host 127.0.0.1 --port 8765
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

## Chrome Extension

1. Run the local agent API on `127.0.0.1:8765`.
2. Open Chrome `chrome://extensions`.
3. Enable Developer mode.
4. Click Load unpacked and select the `extension/` directory.
5. Paste demo samples into ChatGPT, Gmail, or the local demo upload page.

Run the demo upload page:

```bash
python3 -m http.server 8080 -d demo
```

Open:

```text
http://127.0.0.1:8080/upload_page.html
```

JavaScript tests:

```bash
npm test
```

## Current Next Step

Follow `MVP_DEVELOPMENT_PLAN.md` from Phase 0 onward.
