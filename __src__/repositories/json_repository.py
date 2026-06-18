"""Generic JSON file repository with a shared in-memory read cache.

Provides JsonFileRepository for reading and writing JSON files.
Files are cached keyed by resolved path; the cache entry stores (mtime_ns, data)
so freshness is checked by a single integer comparison rather than reloading.
Writes invalidate the entry and trigger a fresh load on the next read.

``read_list_from_path_ro`` returns the cached reference directly; callers MUST NOT
mutate the result or any nested object.  ``read_from_path`` returns a deep copy
for dict-rooted files when mutation by the caller is acceptable.

The cache is bounded (``_MAX_CACHE_ENTRIES``) and evicts the oldest entry (FIFO)
when the limit is reached.  Writes and evictions are protected by a module-level
lock; reads use only GIL-safe dict.get() and are therefore lock-free on CPython.

Serialisation transparently handles str, int, float, bool, None, date, datetime and time.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import copy
import json
import logging
import threading
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any, cast

from shared.exception_util import JsonFileRepositoryError
from shared.path_util import make_all_folders_if_not_exists

# -----------------------------------------------------------------------------
# JSON codec helpers
# -----------------------------------------------------------------------------


class _JsonEncoder(json.JSONEncoder):
    """Extend the standard encoder to serialise date, datetime and time."""

    def default(self, o: object) -> object:
        """Convert date/datetime/time to a tagged JSON object.

        Args:
            o: The Python object to serialise.

        Returns:
            A dict with ``__type__`` and ``value`` keys for temporal types,
            or delegates to the parent encoder for all other types.
        """
        if isinstance(o, datetime):
            return {"__type__": "datetime", "value": o.isoformat()}
        if isinstance(o, date):
            return {"__type__": "date", "value": o.isoformat()}
        if isinstance(o, time):
            return {"__type__": "time", "value": o.isoformat()}
        if isinstance(o, Enum):
            return str(o.value)
        return super().default(o)


def _decode_hook(raw: dict[str, Any]) -> dict[str, Any] | date | datetime | time:
    """Reconstruct date, datetime or time from a tagged JSON object.

    Called by ``json.loads`` for every decoded dict.  Dicts without a
    recognised ``__type__`` tag are returned unchanged.

    Args:
        raw: A decoded JSON object that may contain a ``__type__`` tag.

    Returns:
        The reconstructed Python temporal object, or *raw* unchanged.
    """
    type_tag = raw.get("__type__")
    if type_tag == "datetime":
        return datetime.fromisoformat(raw["value"])
    if type_tag == "date":
        return date.fromisoformat(raw["value"])
    if type_tag == "time":
        return time.fromisoformat(raw["value"])
    return raw


# -----------------------------------------------------------------------------
# Module-level cache shared by all JsonFileRepository instances/subclasses.
# Each entry maps a resolved path string to a 2-tuple: mtime in nanoseconds + parsed data.
# Eviction: FIFO when count exceeds _MAX_CACHE_ENTRIES (Python 3.7+ dicts are insertion-ordered).
# Thread safety: writes are locked; reads use GIL-safe dict.get (atomic on CPython).
# -----------------------------------------------------------------------------

_MAX_CACHE_ENTRIES: int = 2048
_file_cache: dict[str, tuple[int, Any]] = {}
_cache_lock: threading.Lock = threading.Lock()

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class JsonFileRepository:
    """Read/write JSON files backed by a shared, path-keyed in-memory cache.

    All instances and subclasses share the same module-level ``_file_cache``.
    Cache entries store ``(mtime_ns, data)``; on each read the stored mtime is
    compared to the file's current mtime to detect changes with a single integer
    comparison (no string concatenation).

    ``read_from_path`` returns a deep copy so callers may mutate the result freely.
    ``read_list_from_path_ro`` returns the cached reference without copying; its
    caller **must not** mutate the list or any nested object.

    Supported value types beyond native JSON:
        ``date``, ``datetime``, ``time`` — encoded as ISO 8601 tagged objects.
    """

    def __init__(self) -> None:
        """Initialise the repository logger."""
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read_from_path(self, path: Path) -> dict[str, Any]:
        """Return the JSON content of *path*, loading from disk when needed.

        Returns a deep copy of the cached value so callers may mutate it freely.
        Returns ``{}`` when the file does not exist (nothing cached).

        Args:
            path: Path to the JSON file to read.

        Returns:
            A deep copy of the file's JSON content, or ``{}`` when absent.

        Raises:
            JsonFileRepositoryError: When the file exists but is unreadable
                or contains invalid JSON.
        """
        resolved = path.resolve()
        if not resolved.exists():
            self._logger.debug("Fichier JSON absent : '%s'.", resolved)
            return {}

        data = self._get_or_load(resolved, known_mtime_ns=None)
        return cast(dict[str, Any], copy.deepcopy(data))

    def read_list_from_path_ro(self, path: Path, known_mtime_ns: int | None = None) -> list[Any]:
        """Return the JSON list content of *path* without copying.

        The caller **must not** mutate the returned list or any nested object;
        the returned reference is shared with the cache.

        Pass *known_mtime_ns* (e.g. from a prior ``os.scandir()`` call) to skip
        the ``stat()`` call entirely on cache hits — useful for bulk directory scans
        where all mtimes are already available from a single directory pass.

        Args:
            path: Path to the JSON file containing a list at the root level.
            known_mtime_ns: Pre-fetched mtime in nanoseconds, or ``None`` to stat
                the file on demand.

        Returns:
            The cached list reference, or ``[]`` when the file is absent.

        Raises:
            JsonFileRepositoryError: When the file exists but is unreadable
                or contains invalid JSON.
        """
        resolved = path.resolve()
        if not resolved.exists():
            self._logger.debug("Fichier JSON absent : '%s'.", resolved)
            return []

        return cast(list[Any], self._get_or_load(resolved, known_mtime_ns=known_mtime_ns))

    def write_from_dict(self, path: Path, data: dict[str, Any] | list[Any]) -> None:
        """Serialise *data* to *path* as JSON and invalidate any cache entry.

        Parent directories are created automatically.  On success the cache
        entry for this path is removed so the next ``read`` reloads from disk.

        Args:
            path: Destination JSON file path.
            data: Data to serialise.  Values may include str, int, float,
                bool, list, dict, None, date, datetime or time.

        Raises:
            JsonFileRepositoryError: When the file cannot be written.
        """
        resolved = path.resolve()
        self._logger.debug("Écriture du fichier JSON : '%s'.", resolved)

        try:
            make_all_folders_if_not_exists(resolved, is_file_path=True)
            with resolved.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=4, ensure_ascii=False, cls=_JsonEncoder)
        except OSError as exc:
            self._logger.error("Impossible d'écrire '%s'.", resolved, exc_info=True)
            raise JsonFileRepositoryError(resolved, str(exc)) from exc

        # Invalidate cache for this path so the next read reflects persisted content.
        key = str(resolved)
        with _cache_lock:
            _file_cache.pop(key, None)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_load(self, resolved: Path, known_mtime_ns: int | None) -> dict[str, Any] | list[Any]:
        """Return cached data or load from disk.

        Uses *known_mtime_ns* when provided (e.g. from ``os.scandir()``) to avoid
        a redundant ``stat()`` call.  Falls back to ``stat()`` otherwise.

        The expensive disk read and JSON parse happen outside the lock so other
        threads are not blocked.  Two threads may concurrently load the same file
        on a cache miss; the second store simply overwrites the first (same data).

        Args:
            resolved: Fully resolved, existing file path.
            known_mtime_ns: Pre-fetched mtime in nanoseconds, or ``None``.

        Returns:
            The cached (or freshly loaded) data object.
        """
        key = str(resolved)
        current_mtime = known_mtime_ns if known_mtime_ns is not None else resolved.stat().st_mtime_ns

        # Fast read-only check — GIL-safe on CPython, no lock needed.
        entry = _file_cache.get(key)
        if entry is not None and entry[0] == current_mtime:
            self._logger.debug("Cache hit : '%s'.", resolved.name)
            return entry[1]

        # Cache miss or stale entry: load outside the lock.
        data = self._load_from_disk(resolved)

        # Store with lock; evict oldest entry (FIFO) when the cache is full.
        with _cache_lock:
            _file_cache[key] = (current_mtime, data)
            if len(_file_cache) > _MAX_CACHE_ENTRIES:
                oldest = next(iter(_file_cache))
                del _file_cache[oldest]

        return data

    def _load_from_disk(self, resolved: Path) -> dict[str, Any] | list[Any]:
        """Read and deserialise a JSON file; raises on I/O or parse errors.

        Args:
            resolved: Fully resolved path to an existing JSON file.

        Returns:
            The deserialised content (dict or list depending on the file root type).

        Raises:
            JsonFileRepositoryError: When the file cannot be opened or parsed.
        """
        try:
            with resolved.open(encoding="utf-8") as fh:
                data = json.load(fh, object_hook=_decode_hook)
            self._logger.debug("Fichier JSON chargé depuis le disque : '%s'.", resolved)
        except Exception as exc:
            self._logger.error("Lecture impossible pour '%s'.", resolved, exc_info=True)
            raise JsonFileRepositoryError(resolved, str(exc)) from exc
        else:
            return data


# EOF
