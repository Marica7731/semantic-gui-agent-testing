"""Platform-neutral executor interface and the optimized act pipeline.

Subclasses only implement raw device primitives (dump / tap / type / back);
the semantic locate-act-wait-assert pipeline lives here so every platform
gets the same behavior: no hard-coded coordinates, deterministic matching,
and a UI-tree cache for cheap change detection.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from .assertions import ElementExpectation, assert_element
from .models import ActionResult, ElementMatch, Screen, SemanticTarget
from .semantic.incremental import UITreeCache
from .semantic.matcher import MatchResult, SemanticMatcher
from .visual.fallback import VisualFallback
from .waiting import wait_until


class GUIExecutor(ABC):
    platform = "abstract"

    def __init__(self) -> None:
        self.matcher = SemanticMatcher()
        self.cache = UITreeCache()
        self.visual = VisualFallback()

    # -- primitives each backend must provide -------------------------------
    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def dump_screen(self) -> Screen: ...

    @abstractmethod
    def tap_point(self, x: int, y: int) -> None: ...

    @abstractmethod
    def type_text(self, text: str) -> None: ...

    @abstractmethod
    def press_back(self) -> None: ...

    def screenshot(self) -> bytes:
        raise NotImplementedError(f"{self.platform} executor does not support screenshots")

    # -- shared pipeline ----------------------------------------------------
    def __enter__(self) -> "GUIExecutor":
        self.connect()
        return self

    def __exit__(self, *exc: object) -> bool:
        self.disconnect()
        return False

    def screen(self) -> Screen:
        screen = self.dump_screen()
        self.cache.update(screen.root)
        return screen

    def find(self, target: SemanticTarget) -> MatchResult:
        return self.matcher.match(self.screen(), target)

    def tap(self, target: SemanticTarget) -> ActionResult:
        start = time.perf_counter()
        result = self.matcher.match(self.screen(), target)
        best = result.best
        if best is None:
            return self._fail("tap", target.id, "no matching element", start)
        x, y = best.node.center()
        self.tap_point(x, y)
        detail = f"matched via {best.matched_via}"
        if result.ambiguous:
            detail += f"; ambiguous ({len(result.matches)} candidates), used best"
        return self._ok("tap", target.id, detail, start)

    def input_text(self, text: str, target: SemanticTarget | None = None) -> ActionResult:
        start = time.perf_counter()
        if target is not None:
            tap_result = self.tap(target)
            if not tap_result.success:
                return tap_result
        self.type_text(text)
        return self._ok("input_text", target.id if target else "", text, start)

    def back(self) -> ActionResult:
        start = time.perf_counter()
        self.press_back()
        return self._ok("back", "", "", start)

    def wait_for(
        self,
        target: SemanticTarget,
        timeout_s: float = 10.0,
        poll_interval_s: float = 0.5,
    ) -> ElementMatch:
        return wait_until(
            lambda: self.matcher.match(self.screen(), target).best,
            timeout_s=timeout_s,
            poll_interval_s=poll_interval_s,
            message=f"element '{target.id}' not found",
        )

    def assert_state(self, target: SemanticTarget, expectation: ElementExpectation) -> None:
        result = self.matcher.match(self.screen(), target)
        node = result.best.node if result.best else None
        assert_element(node, expectation, target_id=target.id)

    # -- helpers ------------------------------------------------------------
    def _ok(self, action: str, target_id: str, detail: str, start: float) -> ActionResult:
        return ActionResult(
            action=action,
            success=True,
            target_id=target_id,
            detail=detail,
            elapsed_ms=(time.perf_counter() - start) * 1000,
        )

    def _fail(self, action: str, target_id: str, error: str, start: float) -> ActionResult:
        return ActionResult(
            action=action,
            success=False,
            target_id=target_id,
            error=error,
            elapsed_ms=(time.perf_counter() - start) * 1000,
        )
