"""Module contenant le presentateur pour la modification de fournisseur."""

from typing import Any, Callable, Dict, Optional

from models.provider_model import ProviderModel
from presenters.workflow_builder_presenter import WorkflowBuilderPresenter
from services.provider_service import ProviderService
from services.workflow_service import WorkflowService
from views.provider_edit_view import ProviderEditView


class ProviderEditPresenter:
    """Présentateur (Presenter) pour gerer la creation et modification d'un fournisseur.

    Owns both the provider form and the embedded WorkflowBuilderPresenter.
    Steps are delegated entirely to the workflow sub-presenter.
    """

    def __init__(
        self,
        view: ProviderEditView,
        provider_service: ProviderService,
    ) -> None:
        """Initialise le présentateur.

        Args:
            view: L'interface utilisateur de modification.
            service: Le service gérant la logique métier des fournisseurs.
            provider_service: Service de gestion des fournisseurs.
        """
        self._view = view
        self._service = provider_service
        self._is_creation_mode = False
        self._current_provider: Optional[ProviderModel] = None
        self._on_done: Optional[Callable[[], None]] = None

        # Sub-presenter that owns the step list and workflow execution.
        self._workflow_presenter = WorkflowBuilderPresenter(
            view=view.workflow_builder_view,
            service_provider=provider_service,
            workflow_service=WorkflowService(),
        )

        self._bind_view_events()

    def set_on_done_callback(self, callback: Callable[[], None]) -> None:
        """Définit la fonction appelée lorsque la modification/création est terminée/annulée.

        Args:
            callback: Callback to invoke on completion.
        """
        self._on_done = callback

    def _bind_view_events(self) -> None:
        """Wires the Save and Cancel buttons to their handlers."""
        self._view.set_callbacks(
            on_save=self._on_save,
            on_cancel=self._on_cancel,
        )

    def create_new(self) -> None:
        """Passe le presentateur en mode creation et charge un modele vide."""
        self._is_creation_mode = True
        self._current_provider = ProviderModel.get_default_data()

        # Initialize an empty workflow for the new provider.
        self._workflow_presenter.init_new(self._current_provider.id_file)
        self._view.load_data(self._provider_to_dict(self._current_provider))

    def load_provider(self, id_file: str) -> None:
        """Passe le presentateur en mode modification et charge le modele specifie.

        Args:
            id_file: L'ID fichier du fournisseur à supprimer.
        """
        self._is_creation_mode = False
        self._current_provider = self._service.get_provider(id_file)

        # Load existing workflow steps from the repository.
        self._workflow_presenter.load(self._current_provider.id_file)
        self._view.load_data(self._provider_to_dict(self._current_provider))

    def _provider_to_dict(self, provider: ProviderModel) -> Dict[str, Any]:
        """Converts provider model fields to a form-data dictionary.

        Args:
            provider: Source provider model.

        Returns:
            Dict with all form-relevant fields.
        """
        return {
            "id_file": provider.id_file,
            "provider_name": provider.provider_name,
            "url": provider.url,
            "version": provider.version,
            "browser_displayed": provider.browser_displayed,
            "automation_obfuscated": provider.automation_obfuscated,
            "created_date": provider.created_date,
            "modified_date": provider.modified_date,
        }

    def _on_save(self, form_data: Dict[str, Any]) -> None:
        """Valide et sauvegarde le fournisseur.

        Args:
            form_data: Les données brutes récupérées de la vue.
        """
        try:
            if not self._current_provider:
                return

            # Merge form data into the provider model.
            self._current_provider.provider_name = form_data["provider_name"]
            self._current_provider.url = form_data["url"]
            self._current_provider.version = form_data["version"]
            self._current_provider.browser_displayed = form_data["browser_displayed"]
            self._current_provider.automation_obfuscated = form_data["automation_obfuscated"]

            # Collect steps from the sub-presenter.
            self._current_provider.steps = self._workflow_presenter.get_steps()

            self._persist_provider()

        except Exception as e:
            self._view.show_error(str(e))

    def _persist_provider(self) -> None:
        """Creates or updates the provider in the service layer."""
        if not self._current_provider:
            return

        if self._is_creation_mode:
            # Cancel when the ID file already exists and the user declines overwrite.
            already_exists = self._service.exists_provider(self._current_provider.id_file)
            if already_exists and not self._view.ask_overwrite_confirmation():
                return
            self._service.create_provider(self._current_provider)
        else:
            self._current_provider.update_modified_date()
            self._service.update_provider(self._current_provider)

        self._view.clear_data()
        if self._on_done:
            self._on_done()

    def _on_cancel(self) -> None:
        """Annule l'action courante."""
        self._view.clear_data()
        self._current_provider = None
        if self._on_done:
            self._on_done()
