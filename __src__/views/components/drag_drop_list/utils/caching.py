"""LRU cache and computed-property helpers."""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, TypeVar

from shared.exception_util import InvalidLruCacheCapacityError

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """Fixed-capacity least-recently-used cache.

    Items are evicted in LRU order when capacity is exceeded.
    Not thread-safe.

    Example:
        >>> cache: LRUCache[str, int] = LRUCache(capacity=128)
        >>> cache.put("x", 42)
        >>> cache.get("x")
        42
    """

    def __init__(self, capacity: int) -> None:
        """Initializes the cache.

        Args:
            capacity: Maximum number of items before eviction. Must be >= 1.

        Raises:
            ValueError: If capacity < 1.
        """
        if capacity < 1:
            raise InvalidLruCacheCapacityError(capacity)
        self._capacity = capacity
        self._cache: OrderedDict[K, V] = OrderedDict()

    # ── Public API ───────────────────────────────────────────────────

    def get(self, key: K) -> V | None:
        """Returns the cached value or None if absent.

        Args:
            key: Cache lookup key.

        Returns:
            Cached value, or None when the key is missing.
        """
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: K, value: V) -> None:
        """Stores a value, evicting the LRU entry when at capacity.

        Args:
            key: Cache key.
            value: Value to store.
        """
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self._capacity:
            self._cache.popitem(last=False)
        self._cache[key] = value

    def invalidate(self, key: K) -> None:
        """Removes a specific key. No-op if absent.

        Args:
            key: The key to remove.
        """
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Evicts all cached entries."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return the number of cached entries."""
        return len(self._cache)
