"""Presenter for the URL source configuration section of the executor panel.

Owns URL preview building logic and the full discover CRUD + compute flow.
Called by ExecutorPresenter when a profile is loaded or any URL-source field changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from models.launcher_model import LaunchModel
from models.urls_discover_entries_model import UrlsDiscoverEntriesModel
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
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

        vm.bind_compute_discovers(self._on_compute_discovers)

    # ------------------------------------------------------------------
    # Public API — called by ExecutorPresenter
    # ------------------------------------------------------------------

    def refresh_preview_for_profile(self, profile: LaunchModel) -> None:
        """Build URL previews / discover state from the profile and push to the VM."""
        # TODO PCO

    def refresh_preview_from_vm(self) -> None:
        """Build URL previews from the live VM state and push them to the VM."""
        # TODO PCO

    def get_current_discovers_hub(self) -> UrlsDiscoverEntriesModel:
        """Return the current discover hub, built from the latest VM state."""
        # TODO PCO

    def _on_compute_discovers(self) -> None:
        """Run the discovery computation and push the result to the VM."""
        # TODO PCO

    def _on_select_discover(self, id_discover: str) -> None:
        """Load the chosen IN row into the VM form and switch to edit mode."""
        # TODO PCO


# EOF
