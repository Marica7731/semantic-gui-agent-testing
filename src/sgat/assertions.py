"""Declarative assertions evaluated locally — no model involvement."""

from __future__ import annotations

from dataclasses import dataclass

from .models import UINode


class AssertionFailed(AssertionError):
    pass


@dataclass
class ElementExpectation:
    exists: bool = True
    text_equals: str | None = None
    text_contains: str | None = None
    enabled: bool | None = None
    clickable: bool | None = None


def assert_element(node: UINode | None, expectation: ElementExpectation, target_id: str = "") -> None:
    label = f"element '{target_id}'" if target_id else "element"

    if expectation.exists:
        if node is None:
            raise AssertionFailed(f"{label}: expected to exist but no match was found")
    elif node is None:
        return  # expected absent, and it is absent

    problems: list[str] = []
    if node is not None:
        if expectation.text_equals is not None and node.text != expectation.text_equals:
            problems.append(f"text is {node.text!r}, expected exactly {expectation.text_equals!r}")
        if expectation.text_contains is not None and expectation.text_contains.lower() not in node.text.lower():
            problems.append(f"text is {node.text!r}, expected to contain {expectation.text_contains!r}")
        if expectation.enabled is not None and node.enabled != expectation.enabled:
            problems.append(f"enabled={node.enabled}, expected {expectation.enabled}")
        if expectation.clickable is not None and node.clickable != expectation.clickable:
            problems.append(f"clickable={node.clickable}, expected {expectation.clickable}")

    if problems:
        raise AssertionFailed(f"{label}: " + "; ".join(problems))
