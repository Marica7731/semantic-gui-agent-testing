"""Polling waits with an injectable clock, so tests never sleep for real."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class WaitTimeout(RuntimeError):
    """Raised when a waited condition did not become true in time."""


def wait_until(
    predicate: Callable[[], T | None],
    *,
    timeout_s: float = 10.0,
    poll_interval_s: float = 0.5,
    message: str = "condition not met",
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Poll ``predicate`` until it returns a truthy value or the timeout expires."""
    start = clock()
    while True:
        outcome = predicate()
        if outcome:
            return outcome
        if clock() - start >= timeout_s:
            raise WaitTimeout(f"{message} (waited {timeout_s:.1f}s)")
        sleep(poll_interval_s)
