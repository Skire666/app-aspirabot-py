"""Contract for the workflow-gestion view used by StepsListPresenter.

Hides the concrete WorkflowView (Tkinter) from the Presenter so that
the Presenter remains testable without a display.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from typing import Protocol

from shared.step_view_item import StepViewItem

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepsListGestionView(Protocol):
    """Subset of WorkflowView consumed by StepsListPresenter.

    Covers inline-form management and step-list population only.
    Domain models (StepScrapingModel) never cross this boundary:
    ``set_available_steps`` and ``show_inline_form`` both work with
    ``StepViewItem`` snapshots.
    """

    def set_available_steps(self, items: list[StepViewItem]) -> None:
        """Forward the step list to the inline form for JUMP_TO_STEP population.

        Args:
            items: Current ordered workflow step snapshots.
        """
        ...

    def show_inline_form(self, item: StepViewItem | None) -> None:
        """Load a step into the inline form and switch to edit mode.

        Args:
            item: View-safe snapshot to pre-fill, or None for a blank creation form.
        """
        ...

    def show_inline_form_errors(self, errors: list[str]) -> None:
        """Display validation errors on the inline form panel.

        Args:
            errors: List of error strings to show on the form.
        """
        ...

    def show_warning(self, message: str) -> None:
        """Display a non-blocking warning message to the user.

        Args:
            message: Text of the warning to show.
        """
        ...


# EOF
