"""Shared memory for inter-agent communication."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import OrderedDict
from typing import Any


@dataclass
class SharedMemory:
    """
    Shared memory store for hive agents.

    Agents can read outputs from other agents without message duplication.
    Implements an LRU-like store with configurable max size.
    """

    max_entries: int = 100
    _store: OrderedDict[str, Any] = field(default_factory=OrderedDict)

    def store(self, key: str, value: Any) -> None:
        """Store a value, evicting oldest if at capacity."""
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def get(self, key: str) -> Any | None:
        """Retrieve a value by key."""
        return self._store.get(key)

    def get_all(self) -> dict[str, Any]:
        """Get all stored items."""
        return dict(self._store)

    def get_by_prefix(self, prefix: str) -> dict[str, Any]:
        """Get all items whose key starts with prefix."""
        return {k: v for k, v in self._store.items() if k.startswith(prefix)}

    def clear(self) -> None:
        """Clear all memory."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return key in self._store
