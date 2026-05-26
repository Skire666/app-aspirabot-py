"""Factory function for building IUrlSourceProvider instances.

Selects the correct concrete provider based on the source type string returned
by ``ScrapingView.get_url_source()``.

Example:
    >>> p = build_url_source_provider("manual", ["https://example.com"])
    >>> p.has_next()
    True
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from interfaces.i_url_source_provider import IUrlSourceProvider
from services.url_sources.csv_url_source import CsvUrlSourceProvider
from services.url_sources.folder_url_source import FolderUrlSourceProvider
from services.url_sources.manual_url_source import ManualUrlSourceProvider
from shared.exception_util import InvalidUrlSourceValueTypeError, UnknownUrlSourceTypeError

# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def build_url_source_provider(
    source_type: str,
    source_value: list[str] | str,
) -> IUrlSourceProvider:
    """Instantiate the appropriate URL source provider for the given type.

    Args:
        source_type: One of ``"manual"``, ``"csv"``, or ``"folder"``.
        source_value: For ``"manual"`` a ``list[str]`` of URLs; for ``"csv"``
            and ``"folder"`` a ``str`` path.

    Returns:
        A concrete ``IUrlSourceProvider`` ready for iteration.

    Raises:
        UnknownUrlSourceTypeError: When ``source_type`` is not recognised.
        InvalidUrlSourceValueTypeError: When ``source_value`` has an incompatible
            type for the requested source.

    Examples:
        >>> build_url_source_provider("manual", ["https://a.com"])
        <ManualUrlSourceProvider ...>
        >>> build_url_source_provider("csv", "/tmp/urls.csv")
        <CsvUrlSourceProvider ...>
        >>> build_url_source_provider("folder", "/tmp/urls")
        <FolderUrlSourceProvider ...>
    """
    if source_type == "manual":
        return _build_manual(source_value)
    if source_type == "csv":
        return _build_csv(source_value)
    if source_type == "folder":
        return _build_folder(source_value)

    raise UnknownUrlSourceTypeError(source_type)


def _build_manual(source_value: list[str] | str) -> ManualUrlSourceProvider:
    """Build a ManualUrlSourceProvider from a list of URLs.

    Args:
        source_value: Must be a ``list[str]``.

    Returns:
        A ``ManualUrlSourceProvider`` instance.

    Raises:
        InvalidUrlSourceValueTypeError: When ``source_value`` is not a list.
    """
    if not isinstance(source_value, list):
        raise InvalidUrlSourceValueTypeError("manual", "list[str]", type(source_value).__name__)
    return ManualUrlSourceProvider(source_value)


def _build_csv(source_value: list[str] | str) -> CsvUrlSourceProvider:
    """Build a CsvUrlSourceProvider from a file path string.

    Args:
        source_value: Must be a ``str`` path to a CSV file.

    Returns:
        A ``CsvUrlSourceProvider`` instance.

    Raises:
        InvalidUrlSourceValueTypeError: When ``source_value`` is not a string.
    """
    if not isinstance(source_value, str):
        raise InvalidUrlSourceValueTypeError("csv", "str", type(source_value).__name__)
    return CsvUrlSourceProvider(source_value)


def _build_folder(source_value: list[str] | str) -> FolderUrlSourceProvider:
    """Build a FolderUrlSourceProvider from a folder path string.

    Args:
        source_value: Must be a ``str`` path to a folder.

    Returns:
        A ``FolderUrlSourceProvider`` instance.

    Raises:
        InvalidUrlSourceValueTypeError: When ``source_value`` is not a string.
    """
    if not isinstance(source_value, str):
        raise InvalidUrlSourceValueTypeError("folder", "str", type(source_value).__name__)
    return FolderUrlSourceProvider(source_value)
