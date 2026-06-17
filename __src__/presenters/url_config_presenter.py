"""Presenter for the URL source configuration section of the executor panel.

Owns URL preview building logic and the full discover CRUD + compute flow.
Called by ExecutorPresenter when a profile is loaded or any URL-source field changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from models.launcher_model import LaunchModel
from models.sourcing_urls.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.sourcing_urls.urls_discover_item_model import UrlsDiscoverItemModel
from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from shared.constants import C_SIZE_HEXASTRING_DISCOVER_ID
from shared.enums import UrlSourceTypeEnum
from shared.random_util import generate_rng_hexastring
from view_models.executor_view_model import DiscoverRowState, ExecutorViewModel

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
        # Stable ID for the single OUT discover item — preserved across profile load/save cycles.
        self._out_discover_id: str = generate_rng_hexastring(C_SIZE_HEXASTRING_DISCOVER_ID)

    # ------------------------------------------------------------------
    # Public API — called by ExecutorPresenter
    # ------------------------------------------------------------------

    def refresh_preview_for_profile(self, profile: LaunchModel) -> None:
        """Build URL previews / discover state from the profile and push to the VM.

        Args:
            profile: The launch profile whose URL source configuration is rendered.
        """
        self._vm.set_discovers_in_rows([])
        source_type = profile.urls_source_type
        if source_type == UrlSourceTypeEnum.E_FOLDER_RACS:
            self._refresh_folder_racs_from_model(profile.urls_folder_racs)
        elif source_type == UrlSourceTypeEnum.E_FOLDER_JSONS:
            self._refresh_folder_jsons_from_model(profile.urls_folder_jsons)
        elif source_type == UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            self._load_discover_hub_into_vm(profile.urls_discover_entries)

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
        elif source_type == UrlSourceTypeEnum.E_FOLDER_JSONS:
            model = UrlsFolderJsonsModel(
                folder_json=self._vm.urls_path_folder_jsons_var.get().strip(),
                orders_json=self._vm.url_sort_order_jsons_var.get(),
            )
            self._refresh_folder_jsons_from_model(model)

    def get_current_discovers_hub(self) -> UrlsDiscoverEntriesModel:
        """Return the current discover hub, built from the latest VM state.

        Returns:
            A UrlsDiscoverEntriesModel reflecting the current IN grid and OUT form.
        """
        return self._build_discover_hub_from_vm()

    def clear_url_state(self) -> None:
        """Clear all URL preview and discover state when no profile is loaded.

        Called by ExecutorPresenter._clear_profile_form() after profile deletion or
        when no profile can be selected.  Clears the IN grid and both folder-mode
        preview lists so the view shows empty content instead of stale data.
        """
        self._vm.set_url_preview_shortcuts([])
        self._vm.set_url_preview_jsons([])
        self._vm.set_discovers_in_rows([])

    # ------------------------------------------------------------------
    # Private — VM action callbacks
    # ------------------------------------------------------------------

    def _on_select_discover(self, id_discover: str) -> None:
        """Load the chosen IN row into the VM form and switch to edit mode.

        Args:
            id_discover: Identifier of the DiscoverModel row to mark as selected.
        """
        self._vm.selected_discover_id_var.set(id_discover)

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
            urls = provider.preview_all_urls()
        except Exception as exc:
            self._logger.error("Erreur lors de la prévisualisation du dossier .url : %s", exc, exc_info=True)
            urls = []
        self._vm.set_url_preview_shortcuts(urls)

    def _refresh_folder_jsons_from_model(self, model: UrlsFolderJsonsModel) -> None:
        """Scan the JSON source folder and push the preview list to the VM.

        Args:
            model: JSON source configuration providing folder path and sort order.
        """
        provider = self._sourcing_urls.get_provider_folder_jsons()
        try:
            provider.setup_model(model)
            urls = provider.preview_all_urls()
        except Exception as exc:
            self._logger.error("Erreur lors de la prévisualisation du dossier .json : %s", exc, exc_info=True)
            urls = []
        self._vm.set_url_preview_jsons(urls)

    # ------------------------------------------------------------------
    # Private — discover hub helpers
    # ------------------------------------------------------------------

    def _load_discover_hub_into_vm(self, hub: UrlsDiscoverEntriesModel) -> None:
        """Populate the VM with an existing discover hub's IN grid and OUT form fields.

        Preserves the OUT item's stable id_discover so save/reload cycles keep the
        same identifier.  Clears the compute message — it will be stale after a load.

        Args:
            hub: The discover hub loaded from the current profile.
        """
        self._out_discover_id = hub.output.id_discover

        rows: list[DiscoverRowState] = [
            DiscoverRowState(
                id_discover=item.id_discover,
                folder_json=item.folder_json,
                pattern_json=item.pattern_json,
                key_mapping=item.key_mapping,
                pattern_urls=item.pattern_urls,
            )
            for item in hub.inputs
        ]
        self._vm.set_discovers_in_rows(rows)

        self._vm.disc_out_pattern_json_var.set(hub.output.pattern_json)
        self._vm.disc_out_key_mapping_var.set(hub.output.key_mapping)
        self._vm.disc_out_pattern_urls_var.set(hub.output.pattern_urls)

    def _build_discover_hub_from_vm(self) -> UrlsDiscoverEntriesModel:
        """Assemble a UrlsDiscoverEntriesModel from the current VM grid and OUT form.

        The OUT item's folder_json is always the current export_folder_var value,
        because the discover output files live in the scraping export directory.

        Returns:
            A UrlsDiscoverEntriesModel ready for validation or compute.
        """
        in_rows = self._vm.get_discovers_in_rows()
        inputs: list[UrlsDiscoverItemModel] = [
            UrlsDiscoverItemModel(
                id_discover=row.id_discover,
                folder_json=row.folder_json,
                pattern_json=row.pattern_json,
                key_mapping=row.key_mapping,
                pattern_urls=row.pattern_urls,
            )
            for row in in_rows
        ]

        out_pattern = self._vm.disc_out_pattern_json_var.get().strip()
        out_key = self._vm.disc_out_key_mapping_var.get().strip()
        out_urls = self._vm.disc_out_pattern_urls_var.get().strip()

        if not out_pattern and not out_key and not out_urls:
            output: UrlsDiscoverItemModel | None = None
        else:
            output = UrlsDiscoverItemModel(
                id_discover=self._out_discover_id,
                # OUT files always live in the scraping export folder.
                folder_json=self._vm.export_folder_var.get().strip(),
                pattern_json=out_pattern,
                key_mapping=out_key,
                pattern_urls=out_urls,
            )

        return UrlsDiscoverEntriesModel(inputs=inputs, output=output)


# EOF
