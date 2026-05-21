"""Contract for the workflow-gestion view used by StepsListPresenter.

Hides the concrete WorkflowView (Tkinter) from the Presenter so that
the Presenter remains testable without a display.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from typing import Protocol

from models.step_scraping_model import StepScrapingModel

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class IStepsListGestionView(Protocol):
    """Subset of WorkflowView consumed by StepsListPresenter.

    Covers inline-form management and step-list population only.
    """

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        """Forward the step list to the inline form for JUMP_TO_STEP population.

        Args:
            steps: Current ordered workflow step list.
        """
        ...

    def show_inline_form(self, step: StepScrapingModel | None) -> None:
        """Load a step into the inline form and switch to edit mode.

        Args:
            step: Existing step to pre-fill, or None for a blank creation form.
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
