"""Presenter that wires the WorkflowBuilderView to the workflow service and repository.

Manages the in-memory step list, opens the inline step form through the
view, and persists changes via the repository.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from typing import Any

from interfaces.i_steps_list_crud_view import IStepsListCrudView
from interfaces.i_steps_list_gestion_view import IStepsListGestionView
from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from presenters.step_label_formatters import format_step_label
from services.scenarios_service import ScenariosService
from services.workflow_service import WorkflowService
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_NOT_FOUND_FOR_UPDATE
from shared.random_util import generate_rng_id_step
from shared.step_registry import build_params
from shared.step_view_item import StepViewItem

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class StepsListPresenter:
    """Orchestrates the workflow list view with service and repository.

    Responsibilities:
    - Loads and caches workflow steps from the repository.
    - Mediates add / edit / delete / move operations via the inline form.
    - Converts StepScrapingModel → StepViewItem before every view call so
      no domain model ever crosses the view boundary.

    Attributes:
        _view: The embedded workflow list widget.
        _service_scenario: Manages provider-related operations.
        _edit_index: Index of the step being edited, or None in add mode.
    """

    def __init__(
        self,
        view: IStepsListCrudView,
        service_scenario: ScenariosService,
        workflow_service: WorkflowService,
        gestion_view: IStepsListGestionView,
    ) -> None:
        """Initializes the presenter and binds view callbacks.

        Args:
            view: The step-list view implementing IStepsListCrudView.
            service_scenario: ScenariosService for provider-related operations.
            workflow_service: WorkflowService used to validate each step on confirm.
            gestion_view: View that owns show_inline_form / set_available_steps.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._gestion_view: IStepsListGestionView = gestion_view
        self._service_scenario: ScenariosService = service_scenario
        self._workflow_service: WorkflowService = workflow_service

        self._scenario_id_file: str | None = None
        self._steps: list[StepScrapingModel] = []
        self._edit_index: int | None = None
        self._is_new_scenario: bool = False

        self._bind_view_events()

    def _bind_view_events(self) -> None:
        """Registers presenter handlers as view callbacks."""
        self._view.on_edit_step = self._on_edit_step
        self._view.on_delete_step = self._on_delete_step
        self._view.on_move_step = self._on_move_step
        self._view.on_toggle_active_step = self._on_toggle_active_step
        self._view.on_reorder_steps = self._on_reorder_steps
        self._view.on_confirm_create_step = self._on_confirm_create_step
        self._view.on_confirm_update_step = self._on_confirm_update_step
        self._view.on_cancel_inline_step = self._on_cancel_inline_step
        self._view.on_clear_all_steps = self._on_clear_all_steps
        self._view.on_duplicate_step = self._on_duplicate_step

    # ---------------------------------------------------------------
    # Public API called by WorkflowPresenter
    # ---------------------------------------------------------------

    def load(self, id_scenario: str) -> None:
        """Loads the workflow for an existing scenario from the repository.

        Args:
            id_scenario: GUID of the scenario to load.
        """
        self._scenario_id_file = id_scenario
        self._is_new_scenario = False
        self._scenario_content: ScenarioModel = self._service_scenario.read_scenario(id_scenario)
        self._steps = list(self._scenario_content.steps)
        self._refresh_view()
        self._view.set_validation_status("Vérification : --", False)

    def init_new(self, id_scenario: str) -> None:
        """Initializes an empty workflow for a brand-new provider.

        Args:
            id_scenario: GUID of the new provider.
        """
        self._scenario_id_file = id_scenario
        self._is_new_scenario = True
        self._steps = []
        self._refresh_view()
        self._view.set_validation_status("Vérification : --", False)

    def get_steps(self) -> list[StepScrapingModel]:
        """Returns a copy of the current step list.

        Returns:
            Snapshot of the in-memory steps.
        """
        return list(self._steps)

    def validate_steps(self) -> list[str]:
        """Validates the current workflow step list.

        Returns:
            List of validation errors; empty when valid.
        """
        errors: list[str] = []
        # Validate each step in its current order for cross-step consistency.
        for index, step in enumerate(self._steps):
            errors.extend(self._workflow_service.validate_step(index, step, self._steps))
        return errors

    def clear_steps(self) -> None:
        """Clears all steps and refreshes the view."""
        # Reset in-memory state and hide the inline form.
        self._steps.clear()
        self._edit_index = None
        self._refresh_view()

    # ---------------------------------------------------------------
    # View event handlers
    # ---------------------------------------------------------------

    def _on_edit_step(self, index: int) -> None:
        """Shows the inline form pre-filled with the step at the given index.

        Args:
            index: Zero-based index of the step to edit.
        """
        if index < 0 or index >= len(self._steps):
            return
        # Track the index so confirm knows which slot to update.
        self._edit_index = index
        # Build view items so set_available_steps and show_inline_form receive no domain models.
        items = self._build_view_items()
        self._gestion_view.set_available_steps(items)
        self._gestion_view.show_inline_form(items[index])

    def _on_confirm_create_step(self, step_type: StepTypeEnum, params: dict[str, Any]) -> bool:
        """Validates and appends a new step from the inline creation form.

        Args:
            step_type: Type of the new step.
            params: Raw parameter dict read from the form widgets.

        Returns:
            True when the step is accepted; False when it fails validation.
        """
        step = StepScrapingModel(
            step_type=step_type, step_id=generate_rng_id_step(), is_active=True, params=build_params(step_type, params)
        )
        # Validate in context of the full list with the new step appended.
        candidate_steps = list(self._steps)
        candidate_steps.append(step)
        target_index = len(self._steps)
        candidate_errors = self._validate_solo_step(candidate_steps, target_index)

        if candidate_errors:
            if self._gestion_view:
                self._gestion_view.show_inline_form_errors(candidate_errors)
            return False

        self._steps.append(step)
        step.mark_as_modified()
        self._edit_index = None
        self._view.clear_selection()
        self._refresh_view()
        return True

    def _on_confirm_update_step(self, step_type: StepTypeEnum, params: dict[str, Any]) -> bool:
        """Validates and replaces the step currently being edited.

        Args:
            step_type: Possibly changed step type from the form.
            params: Raw parameter dict read from the form widgets.

        Returns:
            True when the step is accepted; False when it fails validation.
        """
        if self._edit_index is None or self._edit_index >= len(self._steps):
            if self._gestion_view:
                self._gestion_view.show_warning(C_STEP_NOT_FOUND_FOR_UPDATE)
            return True

        existing = self._steps[self._edit_index]
        step = StepScrapingModel(
            step_type=step_type,
            step_id=existing.step_id,
            is_active=existing.is_active,
            params=build_params(step_type, params),
        )
        # Validate in context of the full list with the updated step in place.
        candidate_steps = list(self._steps)
        candidate_steps[self._edit_index] = step
        candidate_errors = self._validate_solo_step(candidate_steps, self._edit_index)

        if candidate_errors:
            if self._gestion_view:
                self._notify_validation_feedback(candidate_errors[0] if candidate_errors else None)
                self._gestion_view.show_inline_form_errors(candidate_errors)
            return False
        self._notify_validation_feedback(candidate_errors[0] if candidate_errors else None)

        self._steps[self._edit_index] = step
        step.mark_as_modified()
        self._edit_index = None
        self._view.clear_selection()
        self._refresh_view()
        return True

    def find_step_index_by_id(self, step_id: str) -> int | None:
        """Finds the index of the first step with the given step_id.

        Args:
            step_id: The step_id to search for.

        Returns:
            The zero-based index of the first matching step, or None if not found.
        """
        for index, step in enumerate(self._steps):
            if step.step_id == step_id:
                return index
        return None

    def _on_cancel_inline_step(self) -> None:
        """Clears the pending edit state after the view hides the panel."""
        self._edit_index = None
        self._view.clear_selection()

    def _on_delete_step(self, index: int) -> None:
        """Removes a step by index.

        Args:
            index: Zero-based index of the step to delete.
        """
        if 0 <= index < len(self._steps):
            del self._steps[index]
            self._refresh_view()
            errors = self.validate_steps()
            self._notify_validation_feedback(errors[0] if errors else None)

    def _on_clear_all_steps(self) -> None:
        """Clears all steps and persists the empty workflow."""
        self._steps.clear()
        self._edit_index = None
        self._refresh_view()

    def _on_reorder_steps(self, step_ids: list[str]) -> None:
        """Syncs the in-memory step list after a DragDropList reorder.

        Receives an ordered list of step IDs (no domain models) and rebuilds
        self._steps in matching order.  Called after every DragDropList mutation.
        Does NOT call _refresh_view — the view has already applied the change.

        Args:
            step_ids: The new complete step ID ordering produced by the widget.
        """
        steps_by_id = {s.step_id: s for s in self._steps}
        self._steps = [steps_by_id[sid] for sid in step_ids if sid in steps_by_id]

    def _on_move_step(self, index: int, direction: int) -> None:
        """Swaps a step with its neighbour in the given direction.

        Args:
            index: Zero-based index of the step to move.
            direction: -1 to move up, +1 to move down.
        """
        new_index = index + direction
        if 0 <= new_index < len(self._steps):
            self._steps[index], self._steps[new_index] = (self._steps[new_index], self._steps[index])
            self._refresh_view()

    def _on_duplicate_step(self, item: StepViewItem, idx: int) -> StepViewItem:
        """Returns a view-safe copy of the given step for DragDropList insertion.

        Pre-registers the new StepScrapingModel in self._steps so that the
        subsequent _on_reorder_steps call (fired by the DragDropList after
        inserting the duplicate) can locate it by step_id.

        Args:
            item: View-safe snapshot of the step to duplicate.
            idx: Index of the original step in the list.

        Returns:
            A StepViewItem for the new copy.
        """
        original = next((s for s in self._steps if s.step_id == item.step_id), None)
        if original is None:
            return item
        new_step = original.copy_business()
        # Pre-register before the DragDropList fires on_reorder.
        self._steps.insert(idx + 1, new_step)
        context_ids = {s.step_id: i for i, s in enumerate(self._steps)}

        obj_view = self._to_view_item(new_step, idx + 1, context_ids)
        errors = self.validate_steps()
        self._notify_validation_feedback(errors[0] if errors else None)
        return obj_view

    def _on_toggle_active_step(self, index: int) -> None:
        """Toggles the is_active state of a step.

        Args:
            index: Zero-based index of the step to toggle.
        """
        if 0 <= index < len(self._steps):
            self._steps[index].is_active = not self._steps[index].is_active
            self._steps[index].mark_as_modified()
            self._refresh_view()

    # ---------------------------------------------------------------
    # Persist and refresh helpers
    # ---------------------------------------------------------------

    def _refresh_view(self) -> None:
        """Converts self._steps to StepViewItems and updates the view."""
        items = self._build_view_items()
        self._view.render_steps(items)
        self._gestion_view.set_available_steps(items)

    def _notify_validation_feedback(self, first_error: str | None) -> None:
        if first_error:
            self._view.set_validation_status(first_error, True)
        else:
            self._view.set_validation_status("Workflow valide.", False)

    def _validate_solo_step(self, steps: list[StepScrapingModel], candidate_index: int) -> list[str]:
        """Return validation errors for the candidate step within the full workflow context.

        Args:
            steps: Full ordered workflow step list providing cross-step context.
            candidate_index: Index of the step to validate.

        Returns:
            A list of validation errors for the candidate step.
        """
        return self._workflow_service.validate_step(candidate_index, steps[candidate_index], steps)

    # ---------------------------------------------------------------
    # StepViewItem factory helpers
    # ---------------------------------------------------------------

    def _build_view_items(self) -> list[StepViewItem]:
        """Convert the full domain step list to a list of StepViewItems.

        Builds the {step_id: index} context map once so that cross-step
        formatters (e.g. JUMP_TO_STEP) can resolve sibling positions.

        Returns:
            Ordered list of view-safe snapshots matching self._steps.
        """
        context_ids = {s.step_id: i for i, s in enumerate(self._steps)}
        return [self._to_view_item(s, i, context_ids) for i, s in enumerate(self._steps)]

    @staticmethod
    def _to_view_item(step: StepScrapingModel, idx: int, context_ids: dict[str, int]) -> StepViewItem:
        """Convert a single StepScrapingModel to a StepViewItem snapshot.

        Computes the display label eagerly so the View reads it without
        any formatting logic.

        Args:
            step: Domain model to convert.
            idx: Zero-based position of this step in the workflow.
            context_ids: Full {step_id: zero_based_index} mapping for
                cross-step label resolution.

        Returns:
            An immutable StepViewItem containing only view-safe data.
        """
        params_dict = step.params.to_dict()
        label = format_step_label(step.step_type, params_dict, idx, context_ids)
        return StepViewItem(
            step_id=step.step_id,
            step_type=step.step_type,
            is_active=step.is_active,
            modified_date=step.modified_date,
            params_dict=params_dict,
            label=label,
        )


# EOF
