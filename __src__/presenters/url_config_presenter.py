"""Presenter for the URL source configuration section of the executor panel.

Owns URL preview building logic; called by ExecutorPresenter when a profile
is loaded or any editable URL-source field changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from models.launcher_model import LaunchModel
from services.url_sources.url_source_factory import build_url_source_scenario
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import AspirabotBaseError
from view_models.executor_view_model import ExecutorViewModel

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlConfigPresenter:
    """Handles URL source preview refresh for the URL configuration section.

    Owns all URL preview building logic. ExecutorPresenter delegates preview
    updates here instead of handling them directly, keeping its scope limited
    to scenario/profile management and launch orchestration.
    """

    def __init__(self, vm: ExecutorViewModel) -> None:
        """Initialise with the shared ExecutorViewModel.

        Args:
            vm: The executor ViewModel that owns all UI state.
        """
        self._vm = vm
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API — called by ExecutorPresenter
    # ------------------------------------------------------------------

    def refresh_preview_for_profile(self, profile: LaunchModel) -> None:
        """Build URL previews from the profile source and push them to the VM.

        Args:
            profile: The profile whose URL source drives the preview.
        """
        stype = profile.url_source_type
        if stype == UrlSourceTypeEnum.E_FOLDER.value:
            self._update_url_preview_shortcuts(
                profile.url_sources_folder_shortcuts, profile.url_sort_order_shortcuts
            )
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            self._update_url_preview_jsons(
                profile.url_sources_folder_jsons, profile.url_sort_order_jsons
            )

    def refresh_preview_from_vm(self) -> None:
        """Build URL previews from the live VM state and push them to the VM."""
        stype = self._vm.url_source_type_var.get()
        if stype == UrlSourceTypeEnum.E_FOLDER.value:
            self._update_url_preview_shortcuts(
                self._vm.url_source_path_shortcuts_var.get().strip(),
                self._vm.url_sort_order_shortcuts_var.get(),
            )
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            self._update_url_preview_jsons(
                self._vm.url_source_path_jsons_var.get().strip(),
                self._vm.url_sort_order_jsons_var.get(),
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_url_preview_shortcuts(self, path: str, sort_str: str) -> None:
        """Fetch shortcuts-folder preview URLs and push them to the VM.

        Args:
            path: Folder path containing .url shortcut files.
            sort_str: Raw sort-order string.
        """
        if not path:
            self._vm.set_url_preview_shortcuts([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            provider = build_url_source_scenario(UrlSourceTypeEnum.E_FOLDER.value, path, sort)
            self._vm.set_url_preview_shortcuts(provider.preview_url_listed())
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la prévisualisation des URLs (shortcuts)")
            self._vm.set_url_preview_shortcuts([])

    def _update_url_preview_jsons(self, path: str, sort_str: str) -> None:
        """Fetch json-folder preview URLs and push them to the VM.

        Args:
            path: Folder path containing .json files.
            sort_str: Raw sort-order string.
        """
        if not path:
            self._vm.set_url_preview_jsons([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            provider = build_url_source_scenario(UrlSourceTypeEnum.E_JSON.value, path, sort)
            self._vm.set_url_preview_jsons(provider.preview_url_listed())
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la prévisualisation des URLs (jsons)")
            self._vm.set_url_preview_jsons([])

    @staticmethod
    def _parse_sort_order(value: str) -> UrlSortOrderEnum:
        """Convert a sort-order string to its enum member.

        Args:
            value: A raw string matching a UrlSortOrderEnum value.

        Returns:
            The matching enum member, defaulting to E_MTIME_ASC.
        """
        for member in UrlSortOrderEnum:
            if member.value == value:
                return member
        return UrlSortOrderEnum.E_MTIME_ASC


# EOF
