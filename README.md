# semantic-gui-agent-testing

Semantic GUI automation for LLM agents. Drive real Android and Windows UIs
through a single platform-neutral API — **no hard-coded coordinates, no model
calls for element localization**.

Elements are located by meaning (text, content-desc, resource-id/AutomationId,
natural-language description) against the accessibility tree dumped from the
device, with an injectable OCR provider as a last-resort visual fallback.

## Why

LLM-driven GUI agents usually fail on three things: brittle coordinate
scripts, expensive screenshot-per-step vision loops, and flaky waits. This
framework addresses all three:

| Problem | Approach |
| --- | --- |
| Brittle coordinates | Semantic matching over the accessibility tree, deterministic and re-runnable |
| Vision-loop cost | Localization is pure Python — zero model calls; OCR is only a fallback |
| Flaky waits | Polling state waits, declarative assertions, per-step error-isolated batches |

## Components

- **Executors** — `AndroidExecutor` (adb + uiautomator2) and `WindowsExecutor`
  (UI Automation via pywinauto) behind one abstract `GUIExecutor`.
- **Semantic matcher** — deterministic scoring across text / content-desc /
  resource-id / description surfaces, with ambiguity flagging.
- **Incremental UI updates** — Merkle-hash caching so unchanged screens are
  detected without re-processing.
- **Visual fallback** — pluggable OCR provider, used only when the tree fails.
- **MCP server** — expose the executors to any MCP-capable agent over stdio
  (newline-delimited JSON-RPC 2.0, no SDK dependency).
- **Batch + waits + assertions** — execution optimizations for agent loops.
- **Sessions** — per-agent isolation of executor instances and caches.

## Install

Python 3.10+.

```bash
pip install -e .            # core (no device deps)
pip install -e ".[android]" # + uiautomator2
pip install -e ".[windows]" # + pywinauto (Windows only)
pip install -e ".[dev]"     # + pytest
```

## Quickstart (no device needed)

```python
from sgat.models import SemanticTarget
from sgat.registry import default_registry

with default_registry().create("stub") as executor:
    result = executor.tap(SemanticTarget(id="ok", text="OK"))
    print(result.success, result.detail)  # True: matched via text
```

Smoke-test the MCP server against the in-memory stub:

```bash
python -m sgat.mcp.server --executor stub
```

## MCP tools

| Tool | Purpose |
| --- | --- |
| `find_element` | Locate an element semantically, return best match + candidates |
| `tap` | Locate and tap the element center |
| `input_text` | Type text, optionally into a located element |
| `press_back` | Platform back navigation |
| `wait_for` | Poll until an element appears |
| `assert_element` | Assert existence / text / enabled / clickable |

Point an MCP client at a real device:

```
python -m sgat.mcp.server --executor android --serial <serial>
python -m sgat.mcp.server --executor windows --window-title "Notepad"
```

## Status

- **Unit tested**: 16 tests, CI on Ubuntu + Windows, Python 3.10/3.12.
- **Real-device benchmarks**: not yet measured. `benchmarks/run_benchmarks.py`
  is the harness; run it against your devices and record results in
  [docs/benchmarks.md](docs/benchmarks.md). No numbers are published here
  until they come from real runs.

## Documentation

- [AGENTS.md](AGENTS.md) — implementation task brief for AI coding agents
- [docs/architecture.md](docs/architecture.md) — design and data flow
- [docs/deployment.md](docs/deployment.md) — Windows / Android / WSL2 setup
- [docs/selection-rationale.md](docs/selection-rationale.md) — technology choices and why
- [docs/benchmarks.md](docs/benchmarks.md) — metrics definition and result template

## License

[MIT](LICENSE)
