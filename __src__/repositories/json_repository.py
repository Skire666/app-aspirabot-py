"""Generic JSON file repository with a shared in-memory read cache.

Provides JsonFileRepository for reading and writing JSON files.
Already-loaded files are kept in a class-level cache keyed by resolved path;
callers always receive a deep copy.  Serialisation transparently handles
str, int, float, bool, None, date, datetime and time.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import copy
import json
import logging
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any

from shared.exception_util import JsonFileRepositoryError

from __src__.shared.path_util import make_all_folders_if_not_exists

# -----------------------------------------------------------------------------
# JSON codec helpers
# -----------------------------------------------------------------------------


class _JsonEncoder(json.JSONEncoder):
    """Extend the standard encoder to serialise date, datetime and time."""

    def default(self, obj: object) -> object:
        """Convert date/datetime/time to a tagged JSON object.

        Args:
            obj: The Python object to serialise.

        Returns:
            A dict with ``__type__`` and ``value`` keys for temporal types,
            or delegates to the parent encoder for all other types.
        """
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "value": obj.isoformat()}
        if isinstance(obj, date):
            return {"__type__": "date", "value": obj.isoformat()}
        if isinstance(obj, time):
            return {"__type__": "time", "value": obj.isoformat()}
        if isinstance(obj, Enum):
            return str(obj.value)
        return super().default(obj)


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
# Module-level cache shared by all JsonFileRepository instances/subclasses
# -----------------------------------------------------------------------------

_cache: dict[str, dict[str, Any]] = {}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class JsonFileRepository:
    """Read/write JSON files backed by a shared, path-keyed in-memory cache.

    All instances and subclasses share the same module-level ``_cache`` dict
    so any caller benefits from a previously loaded file.  Every ``read`` call
    returns a deep copy to prevent accidental mutation of shared state.

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

        On a cache hit a deep copy of the cached value is returned.
        On a cache miss the file is read, stored in the cache, then a deep
        copy is returned.  When the file does not exist ``{}`` is returned
        and nothing is cached.

        Args:
            path: Path to the JSON file to read.

        Returns:
            A deep copy of the file's JSON content, or ``{}`` when absent.

        Raises:
            JsonFileRepositoryError: When the file exists but is unreadable
                or contains invalid JSON.
        """
        resolved = path.resolve()

        # File absent: nothing to cache, return empty dict.
        if not resolved.exists():
            self._logger.warning("Fichier JSON absent : '%s'.", resolved)
            return {}

        key_cached = str(resolved) + str(Path(resolved).stat().st_mtime)

        # Return a deep copy from cache on hit.
        if key_cached in _cache:
            self._logger.debug("Déjà chargé. Lecture du cache '%s'.", resolved)
            return copy.deepcopy(_cache[key_cached])

        # Load from disk, populate cache, return a deep copy.
        data = self._load_from_disk(resolved)
        _cache[key_cached] = data
        return copy.deepcopy(data)

    def write_from_dict(self, path: Path, data: dict[str, Any]) -> None:
        """Serialise *data* to *path* as JSON and invalidate the cache entry.

        Parent directories are created automatically.  On success the cache
        entry for this path is removed so the next ``read`` reflects the
        persisted content.

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

        # Invalidate stale cache entries for this path (mtime-based keys may not
        # change if write and prior read happen within the filesystem's time-resolution window).
        path_prefix = str(resolved)
        stale = [k for k in _cache if k.startswith(path_prefix)]
        for k in stale:
            del _cache[k]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_from_disk(self, resolved: Path) -> dict[str, Any]:
        """Read and deserialise a JSON file; raises on I/O or parse errors.

        Args:
            resolved: Fully resolved path to an existing JSON file.

        Returns:
            The deserialised content as a dict.

        Raises:
            JsonFileRepositoryError: When the file cannot be opened or parsed.
        """
        try:
            with resolved.open(encoding="utf-8") as fh:
                data: dict[str, Any] = json.load(fh, object_hook=_decode_hook)
            self._logger.debug("Fichier JSON chargé depuis le disque : '%s'.", resolved)
        except (OSError, json.JSONDecodeError) as exc:
            self._logger.error("Lecture impossible pour '%s'.", resolved, exc_info=True)
            raise JsonFileRepositoryError(resolved, str(exc)) from exc
        else:
            return data


# EOF
