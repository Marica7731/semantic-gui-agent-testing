import json

from sgat.mcp.server import McpServer


def test_mcp_initialize_list_and_call():
    server = McpServer("stub")

    init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init["result"]["protocolVersion"] == "2024-11-05"
    assert init["result"]["serverInfo"]["name"] == "semantic-gui-agent-testing"

    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None

    tools = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in tools["result"]["tools"]}
    assert {"find_element", "tap", "input_text", "press_back", "wait_for", "assert_element"} <= names

    call = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "tap", "arguments": {"locator": {"text": "OK"}}},
        }
    )
    assert call["result"]["isError"] is False
    assert json.loads(call["result"]["content"][0]["text"])["success"] is True

    unknown = server.handle(
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope", "arguments": {}}}
    )
    assert unknown["error"]["code"] == -32602
