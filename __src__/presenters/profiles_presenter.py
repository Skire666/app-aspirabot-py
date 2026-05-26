"""Presenter wiring HistoricView to HistoricService."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from models.profile_launch_model import ProfileLaunchModel
from services.profiles_service import ProfilesService
from views.profiles_view import ProfilesView

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesPresenter:
    """Orchestrates the historic panel between HistoryView and HistoryService.

    Loads launch profiles on demand, formats them for the view, and
    delegates the launch action to an injectable hook supplied by main.py.

    Attributes:
        _view: The historic panel view.
        _service: Service that aggregates profiles across providers.
        _last_loaded: Timestamp of the last successful profile load.
        on_request_launch_profile: Optional hook injected from main.py,
            called with (id_provider, id_profile) when the user clicks Lancer.
    """

    def __init__(self, view: ProfilesView, service: ProfilesService) -> None:
        """Initialize the presenter and wire the launch callback on the view.

        Args:
            view: The historic panel view.
            service: Service providing aggregated launch profiles.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._service_profile = service
        self._last_loaded: datetime | None = None
        self._sort_column = "used_date_profile"
        self._sort_ascending = True

        # Hook injected by main.py after construction.
        self.on_request_launch_profile: Callable[[str, str], None] | None = None

        # Register the launch callback immediately so the view is wired.
        self._view.set_on_refresh(self._on_refresh)
        self._view.set_on_launch(self._on_launch)
        self._view.set_on_open_folder(self._on_open_folder)
        self._view.set_on_sort(self._on_sort)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_profiles_loaded(self) -> None:
        """Trigger a profile reload when the tab is shown.

        Reloads if profiles have never been fetched, or if more than one
        second has elapsed since the last successful load.

        Returns:
            None.
        """
        # Skip reload when data is still fresh (within the 1-second window).
        if self._last_loaded and (datetime.now() - self._last_loaded).total_seconds() <= 1:
            return

        self._load_profiles()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_profiles(self) -> None:
        """Fetch, sort, format, and push profiles to the view.

        Returns:
            None.
        """
        # Retrieve all (provider_id, profile) tuples from the service.
        try:
            all_profiles = self._service_profile.list_all_profiles_launch()
        except Exception:
            self._logger.exception("Échec du chargement des profils")
            all_profiles = []

        sorted_tuples = self._sort_profiles(all_profiles)

        # Push formatted rows to the view and stamp the load time.
        path_folder = self._service_profile.get_path_profiles_folder()
        self._view.render_profiles(path_folder, self._format_rows(sorted_tuples))
        self._last_loaded = datetime.now()

    @staticmethod
    def _format_rows(list_profiles: list[ProfileLaunchModel]) -> list[dict[str, Any]]:
        """Convert (provider_id, profile) pairs into DataGrid row dicts.

        Args:
            list_profiles: Sorted list of ProfileLaunchModel instances.

        Returns:
            A list of row dicts ready to pass to render_profiles().
        """
        rows: list[dict[str, Any]] = []

        # Build one dict per profile with a composite id for routing.
        for profile in list_profiles:
            rows.append(profile.export_to_data_json())

        return rows

    def _sort_profiles(self, tuples: list[ProfileLaunchModel]) -> list[ProfileLaunchModel]:
        """Sort profile tuples by the current sort column and direction."""
        col = self._sort_column

        def key_fn(t: ProfileLaunchModel) -> str:
            profile = t
            value = getattr(profile, col, None)
            if col == "launch_count":
                try:
                    return f"{int(value or 0):020d}"
                except TypeError, ValueError:
                    return "0" * 20
            return str(value or "").casefold()

        return sorted(tuples, key=key_fn, reverse=not self._sort_ascending)

    def _on_sort(self, column: str, ascending: bool) -> None:
        """Handle a sort request from the view."""
        self._sort_column = column
        self._sort_ascending = ascending
        self._load_profiles()

    def _on_open_folder(self) -> None:
        """Gère l'événement d'ouverture du dossier des fournisseurs."""
        self._service_profile.open_profiles_folder()

    def _on_refresh(self) -> None:
        """Handle a refresh request from the view."""
        self._load_profiles()

    def _on_launch(self, id_scenario: str, id_profile: str) -> None:
        """Forward a launch request from the view to the injected hook.

        Args:
            id_scenario: ID of the scenario owning the selected profile.
            id_profile: ID of the profile to load and launch.
        """
        if self.on_request_launch_profile:
            self.on_request_launch_profile(id_scenario, id_profile)


# EOF
