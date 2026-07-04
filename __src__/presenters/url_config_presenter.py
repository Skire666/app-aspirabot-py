"""Presenter for the URL source configuration section of the executor panel.

Owns URL preview building logic and the full discover CRUD + compute flow.
Called by ExecutorPresenter when a profile is loaded or any URL-source field changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from models.launcher_model import LaunchModel
from models.sourcing_urls.urls_folder_csv_model import UrlsFolderCsvModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from shared.enums import RelativeDateEnum, UrlSourceTypeEnum
from view_models.executor_view_model import ExecutorViewModel

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlConfigPresenter:
    """Handles URL source preview refresh and discover CRUD/compute for the executor panel.

    Owns all URL preview building logic and the discover hub operations.
    ExecutorPresenter delegates these concerns here.
    """

    def __init__(self, vm: ExecutorViewModel, sourcing_urls: SourcingUrlsService) -> None:
        """Initialise with the shared ExecutorViewModel.

        Args:
            vm: The executor ViewModel that owns all UI state.
            sourcing_urls: Service that provides URL sourcing functionality.
        """
        self._vm = vm
        self._logger = logging.getLogger(__name__)
        self._sourcing_urls = sourcing_urls

    # ------------------------------------------------------------------
    # Public API — called by ExecutorPresenter
    # ------------------------------------------------------------------

    def refresh_preview_for_profile(self, profile: LaunchModel) -> None:
        """Build URL previews from the profile and push to the VM.

        Args:
            profile: The launch profile whose URL source configuration is rendered.
        """
        source_type = profile.urls_source_type
        if source_type == UrlSourceTypeEnum.E_FOLDER_RACS:
            self._refresh_folder_racs_from_model(profile.urls_folder_racs)
        elif source_type == UrlSourceTypeEnum.E_REFRESH_URLS:
            self._refresh_folder_csv_from_model(profile.urls_folder_csv)

    def refresh_preview_from_vm(self) -> None:
        """Build URL previews from the live VM state and push them to the VM.

        Called on every form change so that folder-mode previews stay in sync
        with what the user is typing. No-op for manual and discover modes.
        """
        raw_type = self._vm.urls_source_type_var.get()
        try:
            source_type = UrlSourceTypeEnum(raw_type)
        except ValueError:
            return

        if source_type == UrlSourceTypeEnum.E_FOLDER_RACS:
            model = UrlsFolderRacsModel(
                folder_racs=self._vm.urls_path_folder_racs_var.get().strip(),
                orders_racs=self._vm.url_sort_order_shortcuts_var.get(),
            )
            self._refresh_folder_racs_from_model(model)
        elif source_type == UrlSourceTypeEnum.E_REFRESH_URLS:
            model = UrlsFolderCsvModel(
                self._vm.urls_path_folder_csv_var.get().strip(),
                self._vm.url_sort_order_csv_var.get(),
                self._vm.url_x_top_csv_var.get(),
                self._vm.csv_date_type_used_var.get(),
                RelativeDateEnum.view_to_enum(self._vm.csv_date_start_var.get()),
                RelativeDateEnum.view_to_enum(self._vm.csv_date_end_var.get()),
            )
            self._refresh_folder_csv_from_model(model)

    def clear_url_state(self) -> None:
        """Clear all URL preview and discover state when no profile is loaded.

        Called by ExecutorPresenter._clear_profile_form() after profile deletion or
        when no profile can be selected.  Clears the IN grid and both folder-mode
        preview lists so the view shows empty content instead of stale data.
        """
        self._vm.set_url_preview_shortcuts([])
        self._vm.set_url_preview_jsons([])

    # ------------------------------------------------------------------
    # Private — preview helpers
    # ------------------------------------------------------------------

    def _refresh_folder_racs_from_model(self, model: UrlsFolderRacsModel) -> None:
        """Scan the FOLDER (.url) source and push the preview list to the VM.

        Args:
            model: FOLDER source configuration providing folder path and sort order.
        """
        provider = self._sourcing_urls.get_provider_folder_racs()
        try:
            provider.setup_model(model)
            provider.is_ready_to_consum_urls()
            urls = provider.preview_all_urls()
        except Exception as exc:
            self._logger.error("Erreur lors de la prévisualisation du dossier .url : %s", exc, exc_info=True)
            urls = []
        self._vm.set_url_preview_shortcuts(urls)

    def _refresh_folder_csv_from_model(self, model: UrlsFolderCsvModel) -> None:
        """Scan the JSON source folder and push the preview list to the VM.

        Args:
            model: JSON source configuration providing folder path and sort order.
        """
        provider = self._sourcing_urls.get_provider_folder_csv()
        try:
            provider.setup_model(model)
            provider.is_ready_to_consum_urls()
            urls = provider.preview_all_urls()
        except Exception as exc:
            self._logger.error("Erreur lors de la prévisualisation du dossier .json : %s", exc, exc_info=True)
            urls = []
        self._vm.set_url_preview_jsons(urls)

    # ------------------------------------------------------------------
    # Private — discover hub helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _display_to_relative_date_value(display: str) -> str:
        """Convert a RelativeDateEnum French display string to its stored raw value.

        Args:
            display: French display string shown in the combobox.

        Returns:
            The raw enum value string, or E_UNSET value when display is unrecognised.
        """
        for member in RelativeDateEnum:
            if member.enum_to_view() == display:
                return member.value
        return RelativeDateEnum.E_UNSET.value


# EOF
