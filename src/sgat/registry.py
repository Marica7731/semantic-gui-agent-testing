"""Executor registry with lazy dependency checks.

Platform backends are only imported when created, and their third-party
dependencies are verified up front with a clear install hint instead of a
raw ImportError deep inside a device call.
"""

from __future__ import annotations

import importlib.util
from typing import Any, Callable


class ExecutorRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, tuple[Callable[..., Any], tuple[str, ...]]] = {}

    def register(self, name: str, factory: Callable[..., Any], *, requires: tuple[str, ...] = ()) -> None:
        self._factories[name] = (factory, requires)

    def names(self) -> list[str]:
        return sorted(self._factories)

    def missing_dependencies(self, name: str) -> list[str]:
        if name not in self._factories:
            raise KeyError(f"unknown executor '{name}'")
        return [
            module
            for module in self._factories[name][1]
            if importlib.util.find_spec(module) is None
        ]

    def create(self, name: str, **config: Any):
        if name not in self._factories:
            raise KeyError(f"unknown executor '{name}' (available: {', '.join(self.names())})")
        missing = self.missing_dependencies(name)
        if missing:
            raise RuntimeError(
                f"executor '{name}' is missing dependencies: {', '.join(missing)}. "
                "Install the matching extra, e.g. pip install 'semantic-gui-agent-testing[android]'"
            )
        return self._factories[name][0](**config)


def _create_stub(**config: Any):
    from .stub import StubExecutor

    return StubExecutor(**config)


def _create_android(**config: Any):
    from .android.executor import AndroidExecutor

    return AndroidExecutor(**config)


def _create_windows(**config: Any):
    from .windows.executor import WindowsExecutor

    return WindowsExecutor(**config)


def default_registry() -> ExecutorRegistry:
    registry = ExecutorRegistry()
    registry.register("stub", _create_stub)
    registry.register("android", _create_android, requires=("uiautomator2",))
    registry.register("windows", _create_windows, requires=("pywinauto",))
    return registry
