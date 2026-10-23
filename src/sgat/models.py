"""Platform-independent data models shared by every executor."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class SemanticTarget:
    """What the agent wants to act on, expressed in platform-neutral terms.

    At least one locator hint is required; ``description`` alone is enough —
    the matcher resolves it against text / content-desc / resource-id /
    class-name surfaces of the dumped UI tree.
    """

    id: str
    description: str = ""
    resource_id: str = ""
    text: str = ""
    content_desc: str = ""
    class_name: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("SemanticTarget.id must be a non-empty string")
        hints = (self.description, self.resource_id, self.text, self.content_desc, self.class_name)
        if not any(hint.strip() for hint in hints):
            raise ValueError(
                f"SemanticTarget '{self.id}' needs at least one locator hint "
                "(description / resource_id / text / content_desc / class_name)"
            )


@dataclass
class UINode:
    node_id: str
    class_name: str = ""
    text: str = ""
    content_desc: str = ""
    resource_id: str = ""
    bounds: tuple[int, int, int, int] = (0, 0, 0, 0)
    clickable: bool = False
    enabled: bool = True
    children: list["UINode"] = field(default_factory=list)

    def walk(self) -> Iterator["UINode"]:
        yield self
        for child in self.children:
            yield from child.walk()

    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "class_name": self.class_name,
            "text": self.text,
            "content_desc": self.content_desc,
            "resource_id": self.resource_id,
            "bounds": list(self.bounds),
            "clickable": self.clickable,
            "enabled": self.enabled,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UINode":
        return cls(
            node_id=data["node_id"],
            class_name=data.get("class_name", ""),
            text=data.get("text", ""),
            content_desc=data.get("content_desc", ""),
            resource_id=data.get("resource_id", ""),
            bounds=tuple(data.get("bounds", (0, 0, 0, 0))),
            clickable=data.get("clickable", False),
            enabled=data.get("enabled", True),
            children=[cls.from_dict(child) for child in data.get("children", [])],
        )


@dataclass
class Screen:
    root: UINode
    package: str = ""
    captured_at: float = field(default_factory=time.time)

    def nodes(self) -> list[UINode]:
        return list(self.root.walk())


@dataclass
class ElementMatch:
    node: UINode
    score: float
    matched_via: str


@dataclass
class ActionResult:
    action: str
    success: bool
    target_id: str = ""
    detail: str = ""
    error: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "success": self.success,
            "target_id": self.target_id,
            "detail": self.detail,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }
