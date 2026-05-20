"""Presenter wiring HistoricView to HistoricService."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from models.launch_profile_model import LaunchProfileModel
from services.historic_service import HistoricService
from views.historic_view import HistoricView

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class HistoricPresenter:
    """Orchestrates the historic panel between HistoricView and HistoricService.

    Loads launch profiles on demand, formats them for the view, and
    delegates the launch action to an injectable hook supplied by main.py.

    Attributes:
        _view: The historic panel view.
        _service: Service that aggregates profiles across providers.
        _last_loaded: Timestamp of the last successful profile load.
        on_request_launch_profile: Optional hook injected from main.py,
            called with (id_provider, id_profile) when the user clicks Lancer.
    """

    def __init__(self, view: HistoricView, service: HistoricService) -> None:
        """Initialize the presenter and wire the launch callback on the view.

        Args:
            view: The historic panel view.
            service: Service providing aggregated launch profiles.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._service = service
        self._last_loaded: datetime | None = None
        self._sort_column = "used_date_profile"
        self._sort_ascending = True

        # Hook injected by main.py after construction.
        self.on_request_launch_profile: Callable[[str, str], None] | None = None

        # Register the launch callback immediately so the view is wired.
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
            tuples = self._service.list_all_profiles()
        except Exception:
            self._logger.exception("Failed to load profiles")
            tuples = []

        sorted_tuples = self._sort_tuples(tuples)

        # Push formatted rows to the view and stamp the load time.
        self._view.render_profiles(self._format_rows(sorted_tuples))
        self._last_loaded = datetime.now()

    @staticmethod
    def _format_rows(tuples: list[tuple[str, LaunchProfileModel]]) -> list[dict[str, Any]]:
        """Convert (provider_id, profile) pairs into DataGrid row dicts.

        Args:
            tuples: Sorted list of (provider_id, LaunchProfileModel) pairs.

        Returns:
            A list of row dicts ready to pass to render_profiles().
        """
        rows: list[dict[str, Any]] = []

        # Build one dict per profile with a composite id for routing.
        for id_provider, profile in tuples:
            rows.append(
                {
                    "id": f"{id_provider}:::{profile.id_profile}",
                    "name_profile": profile.name_profile,
                    "url_source_type": profile.url_source_type or "—",
                    "used_date_profile": profile.used_date_profile or "—",
                    "launch_count": str(profile.launch_count),
                    "id_profile": profile.id_profile,
                }
            )

        return rows

    def _sort_tuples(
        self, tuples: list[tuple[str, Any]]
    ) -> list[tuple[str, Any]]:
        """Sort profile tuples by the current sort column and direction."""
        col = self._sort_column

        def key_fn(t: tuple[str, Any]) -> str:
            profile = t[1]
            value = getattr(profile, col, None)
            if col == "launch_count":
                try:
                    return f"{int(value or 0):020d}"
                except (TypeError, ValueError):
                    return "0" * 20
            return str(value or "").casefold()

        return sorted(tuples, key=key_fn, reverse=not self._sort_ascending)

    def _on_sort(self, column: str, ascending: bool) -> None:
        """Handle a sort request from the view."""
        self._sort_column = column
        self._sort_ascending = ascending
        self._last_loaded = None
        self._load_profiles()

    def _on_open_folder(self) -> None:
        """Forward the open-folder request to the service."""
        self._service.open_providers_folder()

    def _on_launch(self, id_provider: str, id_profile: str) -> None:
        """Forward a launch request from the view to the injected hook.

        Args:
            id_provider: ID of the provider owning the selected profile.
            id_profile: ID of the profile to load and launch.
        """
        if self.on_request_launch_profile:
            self.on_request_launch_profile(id_provider, id_profile)


# EOF
