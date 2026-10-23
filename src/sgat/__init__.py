"""semantic-gui-agent-testing: semantic GUI automation for LLM agents.

Android (uiautomator2) and Windows (pywinauto) executors behind one
platform-neutral API, plus an MCP server so any MCP-capable agent can drive
real UIs without hard-coded coordinates.
"""

__version__ = "0.1.0"

from .models import ActionResult, ElementMatch, Screen, SemanticTarget, UINode

__all__ = [
    "ActionResult",
    "ElementMatch",
    "Screen",
    "SemanticTarget",
    "UINode",
    "__version__",
]
