"""Merkle-hash based incremental UI updates.

Every node gets a content hash covering itself and its descendants. When a new
dump arrives, unchanged subtrees are recognized by hash and reused, so an
agent loop can tell at a glance whether the screen it is about to reason about
actually changed. ``node_id`` is excluded from the hash on purpose: identity
comes from content, not dump order.

Note: hash values are recomputed per node on each update, which is fine for
typical UI sizes (hundreds of nodes) but is the known cost center if you ever
feed it tens of thousands of nodes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ..models import UINode


def subtree_hash(node: UINode) -> str:
    """Content hash of a node and all of its descendants."""
    parts = [
        node.class_name,
        node.text,
        node.content_desc,
        node.resource_id,
        ",".join(str(v) for v in node.bounds),
        str(node.clickable),
        str(node.enabled),
    ]
    for child in node.children:
        parts.append(subtree_hash(child))
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()


@dataclass
class CacheStats:
    hits: int = 0
    partial_updates: int = 0
    full_rebuilds: int = 0
    reused_subtrees: int = 0


class UITreeCache:
    """Indexes dumped trees by subtree hash for cheap change detection."""

    def __init__(self) -> None:
        self._by_hash: dict[str, UINode] = {}
        self._root_hash: str | None = None
        self.stats = CacheStats()

    def update(self, root: UINode) -> str:
        """Refresh the cache with a new dump; returns the new root hash."""
        new_hash = subtree_hash(root)
        if new_hash == self._root_hash:
            self.stats.hits += 1
            return new_hash
        if self._root_hash is None:
            self.stats.full_rebuilds += 1
        else:
            self.stats.partial_updates += 1
            self.stats.reused_subtrees += self._count_known_subtrees(root)
        self._index(root)
        self._root_hash = new_hash
        return new_hash

    def lookup(self, digest: str) -> UINode | None:
        return self._by_hash.get(digest)

    def _count_known_subtrees(self, node: UINode) -> int:
        return sum(1 for n in node.walk() if subtree_hash(n) in self._by_hash)

    def _index(self, node: UINode) -> None:
        self._by_hash[subtree_hash(node)] = node
        for child in node.children:
            self._index(child)
