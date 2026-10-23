"""Batch execution with per-step error isolation.

GUI actions are serial by nature; the value here is that one failed step
neither aborts the remaining steps nor throws out of the batch, so agents can
queue many steps and read a single structured report afterwards.
"""

from __future__ import annotations

from typing import Callable, Iterable

from .models import ActionResult


def batch_execute(
    actions: Iterable[Callable[[], ActionResult]],
    *,
    stop_on_error: bool = False,
) -> list[ActionResult]:
    results: list[ActionResult] = []
    for index, action in enumerate(actions):
        try:
            result = action()
        except Exception as exc:  # isolation: one broken step must not kill the batch
            result = ActionResult(
                action=f"batch[{index}]",
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
        results.append(result)
        if stop_on_error and not result.success:
            break
    return results


def summarize(results: list[ActionResult]) -> dict:
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "elapsed_ms": round(sum(r.elapsed_ms for r in results), 2),
    }
