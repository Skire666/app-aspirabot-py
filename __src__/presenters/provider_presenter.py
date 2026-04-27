"""Module contenant le présentateur pour la gestion des fournisseurs."""

from typing import Callable, Dict, List, Optional
from models.provider_model import ProviderModel
from models.provider_validation_report_model import ProviderValidationReport
from services.provider_service import ProviderService
from views.provider_view import ProviderView

class ProviderPresenter:
    """Présentateur (Presenter) pour coordonner la vue et le service des fournisseurs.
    
    Ce présentateur écoute les interactions de la vue, exécute la logique
    métier via le service et met à jour la vue avec les nouvelles données.
    """

    def __init__(self, view: ProviderView, service: ProviderService) -> None:
        """Initialise le présentateur avec sa vue et son service affiliés.

        Args:
            view (ProviderView): L'interface utilisateur.
            service (ProviderService): Le service gérant la logique métier.
        """
        self._view = view
        self._service = service
        self._providers: List[ProviderModel] = []
        self._current_sort_column = "provider_name"
        self._current_sort_ascending = True
        
        # Hooks optionnels injectés depuis le main
        self.on_request_create_provider: Optional[Callable[[], None]] = None
        self.on_request_edit_provider: Optional[Callable[[str], None]] = None

        self._bind_view_events()
        self._load_providers()

    def refresh(self) -> None:
        """Refresh the list of providers."""
        self._load_providers()

    def _bind_view_events(self) -> None:
        """Associe les callbacks de la vue aux méthodes du présentateur."""
        self._view.set_callbacks(
            on_create=self._on_create_provider,
            on_open_folder=self._on_open_folder,
            on_refresh=self._on_refresh,
            on_sort=self._on_sort,
            on_edit=self._on_edit_provider,
            on_launch=self._on_launch_provider,
            on_delete=self._on_delete_provider,
            on_validate=self._on_validate_providers,
        )

    def _load_providers(self) -> None:
        """Charge la liste complète des fournisseurs et met à jour la vue."""
        try:
            self._providers = self._service.list_providers()
        except FileNotFoundError:
            self._providers = []

        self._sort_providers(self._current_sort_column, self._current_sort_ascending)
        self._update_view()

    @staticmethod
    def _text_key(value: str) -> str:
        """Normalizes text values for stable, case-insensitive sorting."""
        return (value or "").lower()

    def _sort_providers(self, column: str, ascending: bool) -> None:
        """Sorts providers in place according to the selected column.

        Args:
            column: Column id used as sort key.
            ascending: True for ascending order.
        """
        if column == "provider_guid":
            self._providers.sort(key=lambda p: self._text_key(p.provider_guid), reverse=not ascending)
        elif column == "provider_name":
            self._providers.sort(key=lambda p: self._text_key(p.provider_name), reverse=not ascending)
        elif column == "url":
            self._providers.sort(key=lambda p: self._text_key(p.url), reverse=not ascending)
        elif column == "created_date":
            self._providers.sort(key=lambda p: self._text_key(p.created_date), reverse=not ascending)
        elif column == "modified_date":
            self._providers.sort(key=lambda p: self._text_key(p.modified_date), reverse=not ascending)

    def _update_view(self) -> None:
        """Transforme les modèles en structures de données simples et rafraîchit la vue."""
        providers_data = self._format_providers(self._providers)
        self._view.render_providers(providers_data)

    def _format_providers(self, providers: List[ProviderModel]) -> List[Dict[str, str]]:
        """Formate une liste de modèles en données tabulaires pour la vue.

        Args:
            providers (List[ProviderModel]): Liste des modèles de fournisseurs.

        Returns:
            List[Dict[str, str]]: Liste formatée pour affichage.
        """
        formatted: List[Dict[str, str]] = []
        for p in providers:
            formatted.append({
                "id": p.provider_guid,
                "provider_guid": p.provider_guid,
                "provider_name": p.provider_name,
                "url": p.url,
                "created_date": p.created_date,
                "modified_date": p.modified_date
            })
        return formatted

    def _on_create_provider(self) -> None:
        """Gère l'événement de création d'un fournisseur depuis la vue."""
        if self.on_request_create_provider:
            self.on_request_create_provider()
        else:
            new_provider = ProviderModel.get_default_data()
            self._service.create_provider(new_provider)
            self._load_providers()
            
    def _on_edit_provider(self, provider_guid: str) -> None:
        """Gère l'événement de modification d'un fournisseur.
        
        Args:
            provider_guid: Le GUID du fournisseur à éditer.
        """
        if self.on_request_edit_provider:
            self.on_request_edit_provider(provider_guid)

    def _on_launch_provider(self, provider_guid: str) -> None:
        """Gère l'événement de lancement d'un fournisseur.
        
        Args:
            provider_guid: Le GUID du fournisseur.
        """
        self._view.show_info('lancement...')

    def _on_delete_provider(self, provider_guid: str) -> None:
        """Gère l'événement de suppression d'un fournisseur.
        
        Args:
            provider_guid: Le GUID du fournisseur à supprimer.
        """
        if self._view.ask_delete_confirmation():
            self._service.delete_provider(provider_guid)
            self._load_providers()

    def _on_open_folder(self) -> None:
        """Gère l'événement d'ouverture du dossier des fournisseurs."""
        self._service.open_providers_folder()

    def _on_refresh(self) -> None:
        """Gère l'événement de rafraîchissement de la liste des fournisseurs."""
        self._load_providers()

    def _on_validate_providers(self) -> None:
        """Validates provider files and displays the validation summary."""
        self._view.set_validation_state(True, "Validation en cours...")

        try:
            report: ProviderValidationReport = self._service.validate_providers()
            self._load_providers()
            self._view.show_validation_report(report)
        except Exception as exc:
            self._view.show_error(f"La validation des fournisseurs a échoué: {exc}")
        finally:
            self._view.set_validation_state(False)

    def _on_sort(self, column: str, ascending: bool) -> None:
        """Trie la liste des fournisseurs et met à jour la vue.

        Args:
            column (str): La colonne sur laquelle trier.
            ascending (bool): Si True le tri est ascendant, sinon descendant.
        """
        self._current_sort_column = column
        self._current_sort_ascending = ascending
        self._sort_providers(column, ascending)
        self._update_view()
