"""Minimal MCP (Model Context Protocol) server over stdio.

Speaks newline-delimited JSON-RPC 2.0 — the standard MCP stdio transport —
and implements the required subset: ``initialize``, ``tools/list`` and
``tools/call``. No third-party SDK is required, and the dispatcher is
transport-agnostic so tests can call ``McpServer.handle`` directly.

Run a smoke test without any device:

    python -m sgat.mcp.server --executor stub

Point an MCP-capable client (e.g. Claude Desktop) at a real device:

    python -m sgat.mcp.server --executor android --serial <serial>
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from ..assertions import ElementExpectation
from ..models import SemanticTarget
from ..registry import default_registry
from ..session import SessionManager
from ..waiting import WaitTimeout

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "semantic-gui-agent-testing", "version": "0.1.0"}

_LOCATOR_FIELDS = ("description", "text", "resource_id", "content_desc", "class_name")


def _locator_schema() -> dict:
    return {
        "type": "object",
        "properties": {field: {"type": "string"} for field in _LOCATOR_FIELDS},
        "anyOf": [{"required": [field]} for field in _LOCATOR_FIELDS],
    }


TOOLS: list[dict] = [
    {
        "name": "find_element",
        "description": "Locate a UI element semantically; returns the best match and top candidates.",
        "inputSchema": {
            "type": "object",
            "properties": {"locator": _locator_schema()},
            "required": ["locator"],
        },
    },
    {
        "name": "tap",
        "description": "Locate an element and tap the center of its bounds.",
        "inputSchema": {
            "type": "object",
            "properties": {"locator": _locator_schema()},
            "required": ["locator"],
        },
    },
    {
        "name": "input_text",
        "description": "Type text, optionally after locating and focusing an element.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "locator": _locator_schema()},
            "required": ["text"],
        },
    },
    {
        "name": "press_back",
        "description": "Press the platform back control.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "wait_for",
        "description": "Poll until an element appears, up to timeout_s.",
        "inputSchema": {
            "type": "object",
            "properties": {"locator": _locator_schema(), "timeout_s": {"type": "number"}},
            "required": ["locator"],
        },
    },
    {
        "name": "assert_element",
        "description": "Assert element state (existence, text, enabled, clickable).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "locator": _locator_schema(),
                "exists": {"type": "boolean"},
                "text_equals": {"type": "string"},
                "text_contains": {"type": "string"},
                "enabled": {"type": "boolean"},
                "clickable": {"type": "boolean"},
            },
            "required": ["locator"],
        },
    },
]


class McpError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _serialize_match(match) -> dict:
    return {"score": round(match.score, 3), "matched_via": match.matched_via, **match.node.to_dict()}


def _serialize_match_result(result) -> dict:
    return {
        "found": result.best is not None,
        "ambiguous": result.ambiguous,
        "best": _serialize_match(result.best) if result.best else None,
        "candidates": [_serialize_match(m) for m in result.matches[:5]],
    }


class McpServer:
    """JSON-RPC dispatcher; transport-agnostic so tests call handle() directly."""

    def __init__(self, executor_name: str = "stub", **executor_config: Any) -> None:
        self._sessions = SessionManager(default_registry())
        self._session = self._sessions.create(executor_name, **executor_config)

    def handle(self, message: dict) -> dict | None:
        method = message.get("method", "")
        if method.startswith("notifications/"):
            return None
        request_id = message.get("id")
        try:
            result = self._dispatch(method, message.get("params") or {})
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except McpError as exc:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": exc.code, "message": str(exc)}}
        except Exception as exc:  # a broken tool call must never crash the server loop
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"{type(exc).__name__}: {exc}"},
            }

    def _dispatch(self, method: str, params: dict) -> dict:
        if method == "initialize":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            }
        if method == "tools/list":
            return {"tools": TOOLS}
        if method == "tools/call":
            return self._call_tool(params)
        raise McpError(-32601, f"method not supported: {method}")

    def _call_tool(self, params: dict) -> dict:
        name = params.get("name", "")
        args = params.get("arguments") or {}
        handlers: dict[str, Callable[[dict], Any]] = {
            "find_element": self._tool_find,
            "tap": self._tool_tap,
            "input_text": self._tool_input_text,
            "press_back": lambda _args: self._session.executor.back().to_dict(),
            "wait_for": self._tool_wait_for,
            "assert_element": self._tool_assert,
        }
        handler = handlers.get(name)
        if handler is None:
            raise McpError(-32602, f"unknown tool: {name}")
        try:
            payload = handler(args)
        except (AssertionError, WaitTimeout) as exc:
            # failed assertions/timeouts are tool outcomes, not protocol errors
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}], "isError": False}

    # -- tool implementations ----------------------------------------------
    def _build_target(self, locator: Any) -> SemanticTarget:
        if not isinstance(locator, dict) or not locator:
            raise McpError(-32602, "locator must be a non-empty object")
        target_id = next(
            (locator[f] for f in ("description", "text", "resource_id") if locator.get(f)),
            "element",
        )
        try:
            return SemanticTarget(id=target_id, **{k: v for k, v in locator.items() if k in _LOCATOR_FIELDS})
        except ValueError as exc:
            raise McpError(-32602, str(exc)) from exc

    def _tool_find(self, args: dict) -> dict:
        target = self._build_target(args.get("locator"))
        executor = self._session.executor
        return _serialize_match_result(executor.matcher.match(executor.screen(), target))

    def _tool_tap(self, args: dict) -> dict:
        target = self._build_target(args.get("locator"))
        return self._session.executor.tap(target).to_dict()

    def _tool_input_text(self, args: dict) -> dict:
        text = args.get("text")
        if not text:
            raise McpError(-32602, "text is required")
        target = self._build_target(args["locator"]) if args.get("locator") else None
        return self._session.executor.input_text(text, target).to_dict()

    def _tool_wait_for(self, args: dict) -> dict:
        target = self._build_target(args.get("locator"))
        match = self._session.executor.wait_for(target, timeout_s=float(args.get("timeout_s", 10.0)))
        return {"found": True, "match": _serialize_match(match)}

    def _tool_assert(self, args: dict) -> dict:
        target = self._build_target(args.get("locator"))
        expectation = ElementExpectation(
            exists=bool(args.get("exists", True)),
            text_equals=args.get("text_equals"),
            text_contains=args.get("text_contains"),
            enabled=args.get("enabled"),
            clickable=args.get("clickable"),
        )
        self._session.executor.assert_state(target, expectation)
        return {"ok": True, "target_id": target.id}


def serve(inputStream, outputStream, executor_name: str, **config: Any) -> None:
    server = McpServer(executor_name, **config)
    for line in inputStream:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            _write(outputStream, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {exc}"}})
            continue
        response = server.handle(message)
        if response is not None:
            _write(outputStream, response)


def _write(stream, payload: dict) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
    stream.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="semantic-gui-agent-testing MCP server")
    parser.add_argument("--executor", default="stub", choices=["stub", "android", "windows"])
    parser.add_argument("--serial", default=None, help="Android device serial (adb)")
    parser.add_argument("--window-title", default="", help="Regex for the target window title (Windows)")
    args = parser.parse_args(argv)

    config: dict[str, Any] = {}
    if args.serial:
        config["serial"] = args.serial
    if args.window_title:
        config["window_title"] = args.window_title
    serve(sys.stdin, sys.stdout, args.executor, **config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
