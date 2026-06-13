"""Presenter for the URL source configuration section of the executor panel.

Owns URL preview building logic and the full discover CRUD + compute flow.
Called by ExecutorPresenter when a profile is loaded or any URL-source field changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from interfaces.i_url_source_provider import IUrlSourceProvider
from models.launcher_model import LaunchModel
from models.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.urls_discover_item_model import UrlsDiscoverItemModel
from models.urls_folder_racs_model import UrlsFolderRacsModel
from services.url_sources.urls_discover_entries_service import UrlsDiscoverEntriesService
from services.url_sources.urls_folder_racs_service import UrlsFolderRacsService
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_DISCOVER_COMPUTE_ERROR,
    C_DISCOVER_COMPUTE_SUCCESS,
    C_DISCOVER_NO_ENTRIES_IN,
    C_DISCOVER_NO_ENTRIES_OUT,
)
from view_models.executor_view_model import DiscoverRowState, ExecutorViewModel

from __src__.models.urls_folder_jsons_model import UrlsFolderJsonsModel
from __src__.services.url_sources.urls_folder_jsons_service import UrlsFolderJsonsService

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlConfigPresenter:
    """Handles URL source preview refresh and discover CRUD/compute for the executor panel.

    Owns all URL preview building logic and the discover hub operations.
    ExecutorPresenter delegates these concerns here.
    """

    def __init__(self, vm: ExecutorViewModel) -> None:
        """Initialise with the shared ExecutorViewModel.

        Args:
            vm: The executor ViewModel that owns all UI state.
            discover_service: Service that performs the URL discovery computation.
        """
        self._vm = vm
        self._logger = logging.getLogger(__name__)

        # Internal state for the discover hub and the last computation result.
        self._discover_entries: UrlsDiscoverEntriesModel = UrlsDiscoverEntriesModel.get_default()
        self._discover_service: UrlsDiscoverEntriesService = UrlsDiscoverEntriesService(self._discover_entries)

        # Register discover action callbacks on the VM.
        vm.bind_select_discover(self._on_select_discover)
        vm.bind_compute_discovers(self._on_compute_discovers)

    # ------------------------------------------------------------------
    # Public API — called by ExecutorPresenter
    # ------------------------------------------------------------------

    def refresh_preview_for_profile(self, profile: LaunchModel) -> None:
        """Build URL previews / discover state from the profile and push to the VM.

        Args:
            profile: The profile whose URL source drives the preview.
        """
        stype = profile.urls_source_type.value
        if stype == UrlSourceTypeEnum.E_FOLDER_RACS.value:
            self._update_url_preview_shortcuts(
                profile.urls_folder_racs.folder_racs, profile.urls_folder_racs.orders_racs
            )
        elif stype == UrlSourceTypeEnum.E_FOLDER_JSONS.value:
            self._update_url_preview_jsons(profile.urls_folder_jsons.folder_json, profile.urls_folder_jsons.orders_json)
        elif stype == UrlSourceTypeEnum.E_DISCOVER_ENTRIES.value:
            self._load_discover_hub_from_profile(profile)

    def refresh_preview_from_vm(self) -> None:
        """Build URL previews from the live VM state and push them to the VM."""
        stype = self._vm.urls_source_type_var.get()
        print(f"refresh_preview_from_vm: stype={stype}")
        if stype == UrlSourceTypeEnum.E_FOLDER_RACS.value:
            self._update_url_preview_shortcuts(
                self._vm.urls_path_folder_racs_var.get().strip(), self._vm.url_sort_order_shortcuts_var.get()
            )
        elif stype == UrlSourceTypeEnum.E_FOLDER_JSONS.value:
            self._update_url_preview_jsons(
                self._vm.urls_path_folder_jsons_var.get().strip(), self._vm.url_sort_order_jsons_var.get()
            )

    def get_current_discovers_hub(self) -> UrlsDiscoverEntriesModel:
        """Return the current discover hub, built from the latest VM state.

        Returns:
            The up-to-date DiscoversHubModel reflecting the form and the IN grid.
        """
        return self._build_hub_from_vm()

    # ------------------------------------------------------------------
    # Discover action handlers — registered on the VM
    # ------------------------------------------------------------------

    def _on_select_discover(self, id_discover: str) -> None:
        """Load the chosen IN row into the VM form and switch to edit mode.

        Args:
            id_discover: Identifier of the entry to load.
        """
        model = next((m for m in self._discover_entries.inputs if m.id_discover == id_discover), None)
        if model is None:
            return
        # Signal edit mode — this triggers the derived can_create/can_modify recompute.
        self._vm.selected_discover_id_var.set(id_discover)

    def _on_compute_discovers(self) -> None:
        """Run the discovery computation and push the result to the VM."""
        hub = self._build_hub_from_vm()
        print(f"_on_compute_discovers: building hub from {len(hub.inputs)} IN rows")
        if not hub.inputs:
            self._vm.discover_compute_message_var.set(C_DISCOVER_NO_ENTRIES_IN)
            return
        if not (hub.output and hub.output.folder_json):
            self._vm.discover_compute_message_var.set(C_DISCOVER_NO_ENTRIES_OUT)
            return
        try:
            self._discover_entries = hub
            self._discover_service.update_sources_and_compute(hub.inputs, hub.output)
            msg = C_DISCOVER_COMPUTE_SUCCESS.format(
                new=len(self._discover_service.new_entries),
                total_in=self._discover_service.input_total_count,
                total_out=self._discover_service.output_total_count,
            )
            self._vm.discover_compute_message_var.set(msg)
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors du calcul de découverte : %s", exc, exc_info=True)
            self._vm.discover_compute_message_var.set(C_DISCOVER_COMPUTE_ERROR.format(exc=exc))

    # ------------------------------------------------------------------
    # Private helpers — discover hub management
    # ------------------------------------------------------------------

    def _load_discover_hub_from_profile(self, profile: LaunchModel) -> None:
        """Populate the VM discover state from the profile's hub.

        Args:
            profile: The profile whose discovers_hub is loaded.
        """
        hub = profile.urls_discover_entries or UrlsDiscoverEntriesModel.get_default()
        self._discover_entries = hub
        self._push_discovers_in_rows()
        self._load_out_form(hub.output)
        self._vm.selected_discover_id_var.set("")
        self._vm.discover_compute_message_var.set("")

    def _push_discovers_in_rows(self) -> None:
        """Map the current hub inputs to DiscoverRowState and push to the VM."""
        rows = [
            DiscoverRowState(
                id_discover=m.id_discover,
                folder_json=m.folder_json,
                pattern_json=m.pattern_json,
                key_mapping=m.key_mapping,
                pattern_urls=m.pattern_urls,
            )
            for m in self._discover_entries.inputs
        ]
        self._vm.set_discovers_in_rows(rows)

    def _build_discover_from_out_form(self) -> UrlsDiscoverItemModel:
        """Build a DiscoverModel from the current VM OUT form Vars.

        Returns:
            A DiscoverModel populated with the current OUT form values.
        """
        model = UrlsDiscoverItemModel.get_default()
        model.folder_json = self._vm.export_folder_var.get().strip()
        model.pattern_json = self._vm.disc_out_pattern_json_var.get().strip()
        model.key_mapping = self._vm.disc_out_key_mapping_var.get().strip()
        model.pattern_urls = self._vm.disc_out_pattern_urls_var.get().strip()
        return model

    def _build_hub_from_vm(self) -> UrlsDiscoverEntriesModel:
        """Build a DiscoversHubModel from the current VM state (IN rows + OUT form).

        Returns:
            A fresh DiscoversHubModel reflecting the current UI state.
        """
        print(f"_build_hub_from_vm: building hub from {len(self._vm.get_discovers_in_rows())} IN rows")
        out_model = self._build_discover_from_out_form()
        inputs = [
            UrlsDiscoverItemModel(
                id_discover=r.id_discover,
                folder_json=r.folder_json,
                pattern_json=r.pattern_json,
                key_mapping=r.key_mapping,
                pattern_urls=r.pattern_urls,
            )
            for r in self._vm.get_discovers_in_rows()
        ]
        return UrlsDiscoverEntriesModel(inputs=inputs, output=out_model)

    def _load_out_form(self, model: UrlsDiscoverItemModel | None) -> None:
        """Populate the OUT form Vars from a DiscoverModel.

        Args:
            model: The OUT model to display; defaults to blank when None.
        """
        m = model or UrlsDiscoverItemModel.get_default()
        with self._vm.batch_update():
            self._vm.disc_out_pattern_json_var.set(m.pattern_json)
            self._vm.disc_out_key_mapping_var.set(m.key_mapping)
            self._vm.disc_out_pattern_urls_var.set(m.pattern_urls)

    # ------------------------------------------------------------------
    # Private helpers — URL preview (shortcuts / jsons)
    # ------------------------------------------------------------------

    def _update_url_preview_shortcuts(self, path_racs: str, sort_str: str) -> None:
        """Fetch shortcuts-folder preview URLs and push them to the VM.

        Args:
            path_racs: Folder path containing .url shortcut files.
            sort_str: Raw sort-order string.
        """
        print(f"_update_url_preview_shortcuts: path_racs={path_racs}, sort_str={sort_str}")
        if not path_racs:
            self._vm.set_url_preview_shortcuts([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            source = UrlsFolderRacsModel(folder_racs=path_racs, orders_racs=sort.value)
            provider: IUrlSourceProvider = UrlsFolderRacsService(source)
            self._vm.set_url_preview_shortcuts(provider.preview_url_listed())
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la prévisualisation des URLs (shortcuts)")
            self._vm.set_url_preview_shortcuts([])

    def _update_url_preview_jsons(self, path_jsons: str, sort_str: str) -> None:
        """Fetch json-folder preview URLs and push them to the VM.

        Args:
            path_jsons: Folder path containing .json files.
            sort_str: Raw sort-order string.
        """
        if not path_jsons:
            self._vm.set_url_preview_jsons([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            source = UrlsFolderJsonsModel(path_jsons, sort.value)
            provider: IUrlSourceProvider = UrlsFolderJsonsService(source)
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
