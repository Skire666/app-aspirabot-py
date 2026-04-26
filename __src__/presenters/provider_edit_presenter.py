"""Module contenant le presentateur pour la modification de fournisseur."""

from typing import Dict, Any, Optional, Callable
from models.provider_model import ProviderModel
from models.step_scrapping_model import StepScrappingModel
from services.provider_service import ProviderService
from services.step_service import StepService
from views.provider_edit_view import ProviderEditView

class ProviderEditPresenter:
    """Présentateur (Presenter) pour gerer la creation et modification d'un fournisseur."""

    def __init__(self, view: ProviderEditView, service: ProviderService) -> None:
        """Initialise le présentateur.

        Args:
            view: L'interface utilisateur de modification.
            service: Le service gérant la logique métier.
        """
        self._view = view
        self._service = service
        self._step_service = StepService()
        self._is_creation_mode = False
        self._current_provider: Optional[ProviderModel] = None
        self._steps: list[StepScrappingModel] = []
        self._on_done: Optional[Callable[[], None]] = None

        self._bind_view_events()

    def set_on_done_callback(self, callback: Callable[[], None]) -> None:
        """Définit la fonction appelée lorsque la modification/création est terminée/annulée."""
        self._on_done = callback

    def _bind_view_events(self) -> None:
        self._view.set_callbacks(
            on_save=self._on_save,
            on_cancel=self._on_cancel,
            on_add_step=self._on_add_step,
            on_edit_step=self._on_edit_step,
            on_delete_step=self._on_delete_step,
            on_move_up=self._on_move_up,
            on_move_down=self._on_move_down,
            on_clear_all=self._on_clear_all,
        )

    def _sync_steps_to_view(self) -> None:
        """Refreshes the workflow list and selection-dependent controls."""
        items = self._step_service.to_view_items(self._steps)
        self._view.render_steps(items)

    def create_new(self) -> None:
        """Passe le presentateur en mode creation et charge un modele vide."""
        self._is_creation_mode = True
        self._current_provider = ProviderModel.get_default_data()
        self._steps = []
        
        data = {
            "provider_guid": self._current_provider.provider_guid,
            "provider_name": self._current_provider.provider_name,
            "url": self._current_provider.url,
            "version": self._current_provider.version,
            "browser_displayed": self._current_provider.browser_displayed,
            "automation_obfuscated": self._current_provider.automation_obfuscated,
            "created_date": self._current_provider.created_date,
            "modified_date": self._current_provider.modified_date
        }
        self._view.load_data(data)
        self._sync_steps_to_view()

    def load_provider(self, provider_guid: str) -> None:
        """Passe le presentateur en mode modification et charge le modele specifie.

        Args:
            provider_guid: Le GUID du fournisseur à éditer.
        """
        self._is_creation_mode = False
        self._current_provider = self._service.get_provider(provider_guid)
        self._steps = list(self._current_provider.steps)
        
        data = {
            "provider_guid": self._current_provider.provider_guid,
            "provider_name": self._current_provider.provider_name,
            "url": self._current_provider.url,
            "version": self._current_provider.version,
            "browser_displayed": self._current_provider.browser_displayed,
            "automation_obfuscated": self._current_provider.automation_obfuscated,
            "created_date": self._current_provider.created_date,
            "modified_date": self._current_provider.modified_date
        }
        self._view.load_data(data)
        self._sync_steps_to_view()

    def _on_save(self, form_data: Dict[str, Any]) -> None:
        """Valide et sauvegarde le fournisseur.

        Args:
            form_data: Les données brutes récupérées de la vue.
        """
        try:
            if not self._current_provider:
                return

            self._current_provider.provider_name = form_data["provider_name"]
            self._current_provider.url = form_data["url"]
            self._current_provider.version = form_data["version"]
            self._current_provider.browser_displayed = form_data["browser_displayed"]
            self._current_provider.automation_obfuscated = form_data["automation_obfuscated"]
            self._current_provider.steps = list(self._steps)

            if self._is_creation_mode:
                # Check for overwrite
                if self._service.exists_provider(self._current_provider.provider_guid):
                    if not self._view.ask_overwrite_confirmation():
                        return
                
                self._service.create_provider(self._current_provider)
            else:
                self._current_provider.update_modified_date()
                self._service.update_provider(self._current_provider)

            self._view.clear_data()
            if self._on_done:
                self._on_done()

        except Exception as e:
            self._view.show_error(str(e))

    def _on_cancel(self) -> None:
        """Annule l'action courante."""
        self._view.clear_data()
        self._steps = []
        self._sync_steps_to_view()
        self._current_provider = None
        if self._on_done:
            self._on_done()

    def _on_add_step(self, step_type: str, value: Any) -> None:
        """Adds a validated step to the workflow."""
        try:
            step = self._step_service.create_step(step_type=step_type, value=value)
            self._steps.append(step)
            self._sync_steps_to_view()
        except ValueError as exc:
            self._view.show_error(str(exc))

    def _on_edit_step(self, index: int, step_type: str, value: Any) -> None:
        """Updates an existing step using validated data."""
        if index < 0 or index >= len(self._steps):
            self._view.show_error("Étape invalide sélectionnée.")
            return

        try:
            step = self._step_service.create_step(step_type=step_type, value=value)
            self._steps[index] = step
            self._sync_steps_to_view()
        except ValueError as exc:
            self._view.show_error(str(exc))

    def _on_delete_step(self, index: int) -> None:
        """Deletes a step from the current workflow."""
        if index < 0 or index >= len(self._steps):
            self._view.show_error("Étape invalide sélectionnée.")
            return

        del self._steps[index]
        self._sync_steps_to_view()

    def _on_move_up(self, index: int) -> None:
        """Moves a step one position up in the workflow."""
        if index <= 0 or index >= len(self._steps):
            return

        self._steps[index - 1], self._steps[index] = self._steps[index], self._steps[index - 1]
        self._sync_steps_to_view()
        self._view.set_selected_step(index - 1)

    def _on_move_down(self, index: int) -> None:
        """Moves a step one position down in the workflow."""
        if index < 0 or index >= len(self._steps) - 1:
            return

        self._steps[index + 1], self._steps[index] = self._steps[index], self._steps[index + 1]
        self._sync_steps_to_view()
        self._view.set_selected_step(index + 1)

    def _on_clear_all(self) -> None:
        """Removes all workflow steps."""
        self._steps = []
        self._sync_steps_to_view()

    def get_step_for_index(self, index: int) -> Optional[StepScrappingModel]:
        """Returns a step by index for optional integrations and tests."""
        if index < 0 or index >= len(self._steps):
            return None
        return self._steps[index]
