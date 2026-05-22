"""Module contenant le présentateur pour la gestion des fournisseurs."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from models.launch_profile_model import LaunchProfileModel
from models.provider_model import ProviderModel
from models.provider_validation_report_model import ProviderValidationReport
from services.provider_service import ProviderService
from views.providers_view import ProvidersView


class ProviderPresenter:
    """Présentateur (Presenter) pour coordonner la vue et le service des fournisseurs.

    Ce présentateur écoute les interactions de la vue, exécute la logique
    métier via le service et met à jour la vue avec les nouvelles données.
    """

    def __init__(self, view: ProvidersView, service: ProviderService) -> None:
        """Initialise le présentateur avec sa vue et son service affiliés.

        Args:
            view (ProviderView): L'interface utilisateur.
            service (ProviderService): Le service gérant la logique métier.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._service = service
        self._last_loaded: datetime | None = None
        self._all_scenarios: list[ProviderModel] = []
        self._current_sort_column = "provider_name"
        self._current_sort_ascending = True

        # Hooks optionnels injectés depuis le main
        self.on_request_create_provider: Callable[[], None] | None = None
        self.on_request_edit_provider: Callable[[str], None] | None = None
        self.on_request_launch_provider: Callable[[str], None] | None = None
        # Guard: returns True when a Workflow edit session is already open.
        self.is_workflow_active: Callable[[], bool] | None = None

        self._bind_view_events()
        self._load_scenarios()

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

        self._load_scenarios()

    def _bind_view_events(self) -> None:
        """Associe les callbacks de la vue aux méthodes du présentateur."""
        self._view.set_callbacks(
            on_create=self._on_create_provider,
            on_open_folder=self._on_open_folder,
            on_refresh=self._on_refresh,
            on_sort=self._on_sort,
            on_edit=self._on_edit_provider,
            on_duplicate=self._on_duplicate_provider,
            on_launch=self._on_launch_provider,
            on_delete=self._on_delete_provider,
            on_validate=self._on_validate_scenarios,
        )

    def _load_scenarios(self) -> None:
        """Charge la liste complète des fournisseurs et met à jour la vue."""
        try:
            self._all_scenarios = self._service.list_all_scenarios()
        except FileNotFoundError:
            self._all_scenarios = []

        self._sort_scenarios(self._current_sort_column, self._current_sort_ascending)
        self._update_view()
        self._last_loaded = datetime.now()

    @staticmethod
    def _text_key(value: str) -> str:
        """Normalizes text values for stable, case-insensitive sorting."""
        return (value or "").casefold()

    def _sort_scenarios(self, column: str, ascending: bool) -> None:
        """Sorts scenarios in place according to the selected column.

        Args:
            column: Column id used as sort key.
            ascending: True for ascending order.
        """
        if column == "id_file":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.id_file), reverse=not ascending)
        elif column == "provider_name":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.provider_name), reverse=not ascending)
        elif column == "provider_desc":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.provider_desc), reverse=not ascending)
        elif column == "created_date_provider":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.created_date_provider), reverse=not ascending)
        elif column == "modified_date_provider":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.modified_date_provider), reverse=not ascending)

    def _update_view(self) -> None:
        """Update the view with the current list of scenarios, sorted and formatted for display."""
        providers_data = self._format_scenarios(self._all_scenarios)
        self._view.render_scenarios(self._service.get_folder_path_scenarios(), providers_data)

    @staticmethod
    def _format_scenarios(providers: list[ProviderModel]) -> list[dict[str, str]]:
        """Formate une liste de modèles en données tabulaires pour la vue.

        Args:
            providers (List[ProviderModel]): Liste des modèles de fournisseurs.

        Returns:
            List[Dict[str, str]]: Liste formatée pour affichage.
        """
        formatted: list[dict[str, str]] = []
        for p in providers:
            formatted.append(
                {
                    "id": p.id_file,
                    "id_file": p.id_file,
                    "provider_name": p.provider_name,
                    "provider_desc": p.provider_desc,
                    "version": p.version,
                    "created_date_provider": p.created_date_provider,
                    "modified_date_provider": p.modified_date_provider,
                }
            )
        return formatted

    def _on_create_provider(self) -> None:
        """Gère l'événement de création d'un fournisseur depuis la vue."""
        # Block creation when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification en cours avant de continuer."
            )
            return
        if self.on_request_create_provider:
            self.on_request_create_provider()
        else:
            new_provider = ProviderModel.get_default_data()
            # Ensure every new provider starts with a default launch profile.
            if not new_provider.launch_profiles:
                new_provider.launch_profiles.append(LaunchProfileModel.get_default())
            self._service.create_provider(new_provider)
            self._load_scenarios()

    def _on_edit_provider(self, id_file: str) -> None:
        """Gère l'événement de modification d'un fournisseur.

        Args:
            id_file: L'ID fichier du fournisseur à éditer.
        """
        # Block edit when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification en cours avant de continuer."
            )
            return
        if self.on_request_edit_provider:
            self.on_request_edit_provider(id_file)

    def _on_launch_provider(self, id_file: str) -> None:
        """Delegates the launch request to the shell via the injected callback.

        Args:
            id_file: The file ID of the provider to launch.
        """
        # Fire the hook injected from main.py, identical pattern to on_request_edit_provider.
        if self.on_request_launch_provider:
            self.on_request_launch_provider(id_file)

    def _on_duplicate_provider(self, id_file: str) -> None:
        """Gère l'événement de duplication d'un fournisseur.

        Args:
            id_file: L'ID fichier du fournisseur à dupliquer.
        """
        if not self._view.ask_duplicate_confirmation():
            return
        try:
            self._service.duplicate_provider(id_file)
            self._load_scenarios()
        except Exception as exc:
            self._logger.error("Erreur lors de la duplication du scénario", exc_info=True)
            self._view.show_error(f"La duplication a échoué : {exc}")

    def _on_delete_provider(self, id_file: str) -> None:
        """Gère l'événement de suppression d'un fournisseur.

        Args:
            id_file: L'ID fichier du fournisseur à supprimer.
        """
        if not self._view.ask_delete_confirmation():
            return
        try:
            self._service.delete_provider(id_file)
            self._load_scenarios()
        except Exception as exc:
            self._logger.error("Erreur lors de la suppression du scénario", exc_info=True)
            self._view.show_error(f"La suppression a échoué : {exc}")

    def _on_open_folder(self, _: str) -> None:
        """Gère l'événement d'ouverture du dossier des fournisseurs."""
        self._service.open_scenarios_folder()

    def _on_refresh(self) -> None:
        """Gère l'événement de rafraîchissement de la liste des fournisseurs."""
        self._load_scenarios()

    def _on_validate_scenarios(self) -> None:
        """Validates provider files and displays the validation summary."""
        self._view.set_validation_state(True, "Validation en cours...")

        try:
            report: ProviderValidationReport = self._service.validate_scenarios()
            self._load_scenarios()
            self._view.show_validation_report(self._format_validation_report(report))
        except Exception as exc:
            self._logger.error("Une erreur s'est produite", exc_info=True)
            self._view.show_error(f"La validation des fournisseurs a échoué: {exc}")
        finally:
            self._view.set_validation_state(False)

    @staticmethod
    def _format_validation_report(report: ProviderValidationReport) -> dict[str, Any]:
        """Converts a domain validation report into a view-friendly dict.

        Args:
            report: Domain model produced by the service.

        Returns:
            Flat dict safe to pass to the view layer.
        """
        return {
            "total_files": report.total_files,
            "valid_files": report.valid_files,
            "invalid_files": report.invalid_files,
            "issues": [
                {
                    "file_name": issue.file_name,
                    "broken_path": issue.broken_path,
                    "reasons": issue.reasons,
                }
                for issue in report.issues
            ],
        }

    def _on_sort(self, column: str, ascending: bool) -> None:
        """Trie la liste des fournisseurs et met à jour la vue.

        Args:
            column (str): La colonne sur laquelle trier.
            ascending (bool): Si True le tri est ascendant, sinon descendant.
        """
        self._current_sort_column = column
        self._current_sort_ascending = ascending
        self._sort_scenarios(column, ascending)
        self._update_view()
