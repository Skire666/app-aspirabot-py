"""Factory function for building IUrlSourceProvider instances.

Selects the correct concrete scenario based on the source type string returned
by ``ExecutorView.get_url_source()``.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from interfaces.i_url_source_provider import IUrlSourceProvider
from services.url_sources.folder_url_source import FolderUrlSourceProvider
from services.url_sources.json_url_source import JsonUrlSourceProvider
from services.url_sources.manual_url_source import ManualUrlSourceProvider
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import InvalidUrlSourceValueTypeError, UnknownUrlSourceTypeError

# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def build_url_source_scenario(
    source_type: str, source_value: list[str] | str, sort_order: UrlSortOrderEnum = UrlSortOrderEnum.E_MTIME_ASC
) -> IUrlSourceProvider:
    """Instantiate the appropriate URL source scenario for the given type.

    Args:
        source_type: One of ``"manual"``, ``"folder"``, or ``"json"``.
        source_value: For ``"manual"`` a ``list[str]`` of URLs; for ``"folder"`` or ``"json"`` a ``str`` path.
        sort_order: File ordering strategy for ``"folder"`` and ``"json"`` sources; ignored for ``"manual"``.

    Returns:
        A concrete ``IUrlSourceProvider`` ready for iteration.

    Raises:
        UnknownUrlSourceTypeError: When ``source_type`` is not recognised.
        InvalidUrlSourceValueTypeError: When ``source_value`` has an incompatible
            type for the requested source.
    """
    if source_type == UrlSourceTypeEnum.E_MANUAL.value:
        return _build_manual(source_value)
    if source_type == UrlSourceTypeEnum.E_FOLDER.value:
        return _build_folder(source_value, sort_order)
    if source_type == UrlSourceTypeEnum.E_JSON.value:
        return _build_json(source_value, sort_order)
    if source_type == UrlSourceTypeEnum.E_DISCOVER.value:
        return _build_manual(source_value)

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


def _build_folder(source_value: list[str] | str, sort_order: UrlSortOrderEnum) -> FolderUrlSourceProvider:
    """Build a FolderUrlSourceProvider from a folder path string.

    Args:
        source_value: Must be a ``str`` path to a folder.
        sort_order: File ordering strategy.

    Returns:
        A ``FolderUrlSourceProvider`` instance.

    Raises:
        InvalidUrlSourceValueTypeError: When ``source_value`` is not a string.
    """
    if not isinstance(source_value, str):
        raise InvalidUrlSourceValueTypeError("folder", "str", type(source_value).__name__)
    return FolderUrlSourceProvider(source_value, sort_order)


def _build_json(source_value: list[str] | str, sort_order: UrlSortOrderEnum) -> JsonUrlSourceProvider:
    """Build a JsonUrlSourceProvider from a folder path string.

    Args:
        source_value: Must be a ``str`` path to a folder containing .json files.
        sort_order: File ordering strategy.

    Returns:
        A ``JsonUrlSourceProvider`` instance.

    Raises:
        InvalidUrlSourceValueTypeError: When ``source_value`` is not a string.
    """
    if not isinstance(source_value, str):
        raise InvalidUrlSourceValueTypeError("json", "str", type(source_value).__name__)
    return JsonUrlSourceProvider(source_value, sort_order)


# EOF
