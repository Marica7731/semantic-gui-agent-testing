import pytest

from sgat.registry import ExecutorRegistry, default_registry
from sgat.session import SessionManager


def test_registry_lists_and_creates_stub():
    registry = default_registry()
    assert registry.names() == ["android", "stub", "windows"]
    executor = registry.create("stub")
    assert executor.platform == "stub"

    scratch = ExecutorRegistry()
    scratch.register("needs-missing", lambda: None, requires=("definitely_not_installed_pkg",))
    assert scratch.missing_dependencies("needs-missing") == ["definitely_not_installed_pkg"]
    with pytest.raises(RuntimeError):
        scratch.create("needs-missing")


def test_sessions_are_isolated():
    manager = SessionManager(default_registry())
    a = manager.create("stub")
    b = manager.create("stub")
    assert a.session_id != b.session_id
    assert a.executor is not b.executor
    assert a.cache is not b.cache
    a.executor.tap_point(1, 2)
    assert b.executor.taps == []
