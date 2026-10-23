"""Per-agent isolated sessions.

Each session lazily owns its own executor instance and UI-tree cache, so two
agents driving the same platform through the framework never share state.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from .semantic.incremental import UITreeCache

if TYPE_CHECKING:
    from .registry import ExecutorRegistry


class AgentSession:
    def __init__(self, registry: "ExecutorRegistry", executor_name: str, config: dict[str, Any]) -> None:
        self.session_id = uuid.uuid4().hex[:12]
        self.executor_name = executor_name
        self.config = dict(config)
        self.cache = UITreeCache()
        self.tags: dict[str, Any] = {}
        self._registry = registry
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            self._executor = self._registry.create(self.executor_name, **self.config)
        return self._executor


class SessionManager:
    def __init__(self, registry: "ExecutorRegistry") -> None:
        self._registry = registry
        self._sessions: dict[str, AgentSession] = {}

    def create(self, executor_name: str, **config: Any) -> AgentSession:
        session = AgentSession(self._registry, executor_name, config)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> AgentSession:
        return self._sessions[session_id]

    def __len__(self) -> int:
        return len(self._sessions)
