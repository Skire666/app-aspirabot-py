"""Presenter for the URL source configuration section of the executor panel.

Owns URL preview building logic and the full discover CRUD + compute flow.
Called by ExecutorPresenter when a profile is loaded or any URL-source field changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from models.discover_model import DiscoverModel
from models.discovers_hub_model import DiscoversHubModel
from models.launcher_model import LaunchModel
from models.urls_computed_model import UrlsComputedModel
from services.discover_service import DiscoverService
from services.url_sources.url_source_factory import build_url_source_scenario
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import C_DISCOVER_COMPUTE_ERROR, C_DISCOVER_COMPUTE_SUCCESS, C_DISCOVER_NO_ENTRIES_IN
from view_models.executor_view_model import DiscoverRowState, ExecutorViewModel

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlConfigPresenter:
    """Handles URL source preview refresh and discover CRUD/compute for the executor panel.

    Owns all URL preview building logic and the discover hub operations.
    ExecutorPresenter delegates these concerns here.
    """

    def __init__(self, vm: ExecutorViewModel, discover_service: DiscoverService) -> None:
        """Initialise with the shared ExecutorViewModel and the DiscoverService.

        Args:
            vm: The executor ViewModel that owns all UI state.
            discover_service: Service that performs the URL discovery computation.
        """
        self._vm = vm
        self._discover_service = discover_service
        self._logger = logging.getLogger(__name__)

        # Internal state for the discover hub and the last computation result.
        self._current_hub: DiscoversHubModel = DiscoversHubModel.get_default()
        self._computed_model: UrlsComputedModel | None = None

        # Register discover action callbacks on the VM.
        vm.bind_add_discover(self._on_add_discover)
        vm.bind_update_discover(self._on_update_discover)
        vm.bind_delete_discover(self._on_delete_discover)
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
        stype = profile.url_source_type
        if stype == UrlSourceTypeEnum.E_FOLDER.value:
            self._update_url_preview_shortcuts(profile.url_sources_folder_shortcuts, profile.url_sort_order_shortcuts)
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            self._update_url_preview_jsons(profile.url_sources_folder_jsons, profile.url_sort_order_jsons)
        elif stype == UrlSourceTypeEnum.E_DISCOVER.value:
            self._load_discover_hub_from_profile(profile)

    def refresh_preview_from_vm(self) -> None:
        """Build URL previews from the live VM state and push them to the VM."""
        stype = self._vm.url_source_type_var.get()
        if stype == UrlSourceTypeEnum.E_FOLDER.value:
            self._update_url_preview_shortcuts(
                self._vm.url_source_path_shortcuts_var.get().strip(), self._vm.url_sort_order_shortcuts_var.get()
            )
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            self._update_url_preview_jsons(
                self._vm.url_source_path_jsons_var.get().strip(), self._vm.url_sort_order_jsons_var.get()
            )

    def get_computed_discover_urls(self) -> list[str]:
        """Return the list of new URLs produced by the last successful computation.

        Returns:
            Ordered list of new URL strings; empty when no computation has run.
        """
        if self._computed_model is None:
            return []
        return list(self._computed_model.new_entries.keys())

    def get_current_discovers_hub(self) -> DiscoversHubModel:
        """Return the current discover hub, built from the latest VM state.

        Returns:
            The up-to-date DiscoversHubModel reflecting the form and the IN grid.
        """
        return self._build_hub_from_vm()

    # ------------------------------------------------------------------
    # Discover action handlers — registered on the VM
    # ------------------------------------------------------------------

    def _on_add_discover(self) -> None:
        """Create a new DiscoverModel from the VM IN form and append it to the hub."""
        new_model = self._build_discover_from_in_form()
        self._current_hub.inputs.append(new_model)
        self._current_hub.mark_as_modified()
        self._push_discovers_in_rows()
        self._clear_in_form()

    def _on_update_discover(self) -> None:
        """Update the row matching selected_discover_id_var with the current IN form."""
        target_id = self._vm.selected_discover_id_var.get()
        updated = self._build_discover_from_in_form(id_discover=target_id)
        self._current_hub.inputs = [updated if m.id_discover == target_id else m for m in self._current_hub.inputs]
        self._current_hub.mark_as_modified()
        self._push_discovers_in_rows()
        self._clear_in_form()
        self._vm.selected_discover_id_var.set("")

    def _on_delete_discover(self, id_discover: str) -> None:
        """Remove the DiscoverModel with the given id from the hub.

        Args:
            id_discover: Identifier of the entry to delete.
        """
        self._current_hub.inputs = [m for m in self._current_hub.inputs if m.id_discover != id_discover]
        self._current_hub.mark_as_modified()
        self._push_discovers_in_rows()
        # If the deleted row was being edited, reset to create mode.
        if self._vm.selected_discover_id_var.get() == id_discover:
            self._clear_in_form()
            self._vm.selected_discover_id_var.set("")

    def _on_select_discover(self, id_discover: str) -> None:
        """Load the chosen IN row into the VM form and switch to edit mode.

        Args:
            id_discover: Identifier of the entry to load.
        """
        model = next((m for m in self._current_hub.inputs if m.id_discover == id_discover), None)
        if model is None:
            return
        with self._vm.batch_update():
            self._vm.disc_in_folder_var.set(model.folder_json)
            self._vm.disc_in_pattern_json_var.set(model.pattern_json)
            self._vm.disc_in_key_mapping_var.set(model.key_mapping)
            self._vm.disc_in_pattern_urls_var.set(model.pattern_urls)
        # Signal edit mode — this triggers the derived can_create/can_modify recompute.
        self._vm.selected_discover_id_var.set(id_discover)

    def _on_compute_discovers(self) -> None:
        """Run the discovery computation and push the result to the VM."""
        hub = self._build_hub_from_vm()
        if not hub.inputs:
            self._vm.discover_compute_message_var.set(C_DISCOVER_NO_ENTRIES_IN)
            self._computed_model = None
            return
        try:
            result = self._discover_service.compute_new_urls(hub)
            self._computed_model = result
            self._current_hub = hub
            msg = C_DISCOVER_COMPUTE_SUCCESS.format(
                new=result.new_url_count, total_in=result.input_unique_count, total_out=result.output_unique_count
            )
            self._vm.discover_compute_message_var.set(msg)
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors du calcul de découverte : %s", exc, exc_info=True)
            self._vm.discover_compute_message_var.set(C_DISCOVER_COMPUTE_ERROR.format(exc=exc))
            self._computed_model = None

    # ------------------------------------------------------------------
    # Private helpers — discover hub management
    # ------------------------------------------------------------------

    def _load_discover_hub_from_profile(self, profile: LaunchModel) -> None:
        """Populate the VM discover state from the profile's hub.

        Args:
            profile: The profile whose discovers_hub is loaded.
        """
        hub = profile.discovers_hub or DiscoversHubModel.get_default()
        self._current_hub = hub
        self._computed_model = None
        self._push_discovers_in_rows()
        self._load_out_form(hub.output)
        self._clear_in_form()
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
            for m in self._current_hub.inputs
        ]
        self._vm.set_discovers_in_rows(rows)

    def _build_discover_from_in_form(self, id_discover: str = "") -> DiscoverModel:
        """Build a DiscoverModel from the current VM IN form Vars.

        Args:
            id_discover: If provided, reuses this identifier; otherwise generates a new one.

        Returns:
            A DiscoverModel populated with the current form values.
        """
        model = DiscoverModel.get_default()
        if id_discover:
            model.id_discover = id_discover
        model.folder_json = self._vm.disc_in_folder_var.get().strip()
        model.pattern_json = self._vm.disc_in_pattern_json_var.get().strip()
        model.key_mapping = self._vm.disc_in_key_mapping_var.get().strip()
        model.pattern_urls = self._vm.disc_in_pattern_urls_var.get().strip()
        return model

    def _build_discover_from_out_form(self) -> DiscoverModel:
        """Build a DiscoverModel from the current VM OUT form Vars.

        Returns:
            A DiscoverModel populated with the current OUT form values.
        """
        model = DiscoverModel.get_default()
        model.folder_json = self._vm.export_folder_var.get().strip()
        model.pattern_json = self._vm.disc_out_pattern_json_var.get().strip()
        model.key_mapping = self._vm.disc_out_key_mapping_var.get().strip()
        model.pattern_urls = self._vm.disc_out_pattern_urls_var.get().strip()
        return model

    def _build_hub_from_vm(self) -> DiscoversHubModel:
        """Build a DiscoversHubModel from the current VM state (IN rows + OUT form).

        Returns:
            A fresh DiscoversHubModel reflecting the current UI state.
        """
        out_model = self._build_discover_from_out_form()
        return DiscoversHubModel(
            inputs=list(self._current_hub.inputs),
            output=out_model,
            created_date=self._current_hub.created_date,
            modified_date=self._current_hub.modified_date,
        )

    def _clear_in_form(self) -> None:
        """Reset the IN form Vars to empty/default values."""
        with self._vm.batch_update():
            self._vm.disc_in_folder_var.set("")
            self._vm.disc_in_pattern_json_var.set("export*.json")
            self._vm.disc_in_key_mapping_var.set("key_xxx")
            self._vm.disc_in_pattern_urls_var.set("https*")

    def _load_out_form(self, model: DiscoverModel | None) -> None:
        """Populate the OUT form Vars from a DiscoverModel.

        Args:
            model: The OUT model to display; defaults to blank when None.
        """
        m = model or DiscoverModel.get_default()
        with self._vm.batch_update():
            self._vm.disc_out_pattern_json_var.set(m.pattern_json)
            self._vm.disc_out_key_mapping_var.set(m.key_mapping)
            self._vm.disc_out_pattern_urls_var.set(m.pattern_urls)

    # ------------------------------------------------------------------
    # Private helpers — URL preview (shortcuts / jsons)
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
