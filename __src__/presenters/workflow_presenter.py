"""Module contenant le presentateur pour la modification de fournisseur."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable
from typing import Any

from models.scenario_model import ProviderModel
from presenters.steps_list_presenter import StepsListPresenter
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.workflow_service import WorkflowService
from shared.random_util import merge_unique_list_id_step
from views.workflow_view import WorkflowView

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WorkflowPresenter:
    """Présentateur (Presenter) pour gerer la creation et modification d'un fournisseur.

    Owns both the provider form and the embedded WorkflowBuilderPresenter.
    Steps are delegated entirely to the workflow sub-presenter.
    """

    def __init__(
        self,
        view: WorkflowView,
        scenarios_service: ScenariosService,
        profiles_service: ProfilesService,
    ) -> None:
        """Initialise le présentateur.

        Args:
            view: L'interface utilisateur de modification.
            service: Le service gérant la logique métier des fournisseurs.
            provider_service: Service de gestion des fournisseurs.
        """
        self._logger = logging.getLogger(__name__)
        self._view: WorkflowView = view
        self._service = scenarios_service
        self._is_creation_mode = False
        self._current_provider: ProviderModel | None = None
        self._on_done: Callable[[], None] | None = None

        # Sub-presenter that owns the step list and workflow execution.
        self._workflow_presenter = StepsListPresenter(
            view=view.workflow_builder_view,
            service_provider=scenarios_service,
            workflow_service=WorkflowService(),
            gestion_view=view,
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
        self._view.show_inline_form(None)

    def load_provider(self, id_file: str) -> bool:
        """Passe le presentateur en mode modification et charge le modele specifie.

        Args:
            id_file: L'ID fichier du fournisseur à supprimer.
        """
        self._is_creation_mode = False

        if not self._service.exists_scenario(id_file):
            self._view.show_error(f"Le fournisseur avec l'ID '{id_file}' n'existe pas.")
            return False

        self._current_provider = self._service.read_scenario(id_file)

        unique_list_id_step: set[str] = set()
        unique_list_id_step.update(
            step.step_id for step in self._current_provider.steps
        )  # Guard against duplicate step IDs.
        merge_unique_list_id_step(unique_list_id_step)

        # Load existing workflow steps from the repository.
        self._workflow_presenter.load(self._current_provider.id_file)
        self._view.load_data(self._provider_to_dict(self._current_provider))
        self._view.show_inline_form(None)
        return True

    @staticmethod
    def _provider_to_dict(provider: ProviderModel) -> dict[str, Any]:
        """Converts provider model fields to a form-data dictionary.

        Args:
            provider: Source provider model.

        Returns:
            Dict with all form-relevant fields.
        """
        return {
            "id_file": provider.id_file,
            "provider_name": provider.provider_name,
            "provider_desc": provider.provider_desc,
            "version": provider.version,
            "created_date_provider": provider.created_date_scenario,
            "modified_date_provider": provider.modified_date_scenario,
        }

    def _on_save(self, form_data: dict[str, Any]) -> None:
        """Valide et sauvegarde le fournisseur.

        Args:
            form_data: Les données brutes récupérées de la vue.
        """
        try:
            if not self._current_provider:
                return

            # Validate workflow steps before persisting.
            errors = self._workflow_presenter.validate_steps()
            if errors:
                self._view.show_error(errors[0])
                return

            # Merge form data into the provider model.
            self._current_provider.provider_name = form_data["provider_name"]
            self._current_provider.provider_desc = form_data["provider_desc"]
            self._current_provider.version = form_data["version"]

            # Collect steps from the sub-presenter.
            self._current_provider.steps = self._workflow_presenter.get_steps()

            self._persist_scenario()

        except Exception as exc:
            self._logger.exception("Une erreur s'est produite", exc_info=True)
            self._view.show_error(str(exc))

    def _persist_scenario(self) -> None:
        """Creates or updates the scenario in the service layer."""
        if not self._current_provider:
            return

        if self._is_creation_mode:
            # Cancel when the ID file already exists and the user declines overwrite.
            already_exists = self._service.exists_scenario(self._current_provider.id_file)
            if already_exists and not self._view.ask_overwrite_confirmation():
                return
            self._service.create_scenario(self._current_provider)
        else:
            self._current_provider.mark_as_modified()
            self._service.update_scenario(self._current_provider)

        self._workflow_presenter.clear_steps()
        self._view.clear_data()
        if self._on_done:
            self._on_done()

    def _on_cancel(self) -> None:
        """Annule l'action courante."""
        # Reset the embedded workflow too: Save already clears it, so Cancel
        # must leave the presenter and view in the same clean state.
        self._workflow_presenter.clear_steps()
        self._view.clear_data()
        self._current_provider = None
        if self._on_done:
            self._on_done()
