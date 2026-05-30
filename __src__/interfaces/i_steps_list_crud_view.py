"""Contract for the step-list CRUD view used by StepsListPresenter.

Hides the concrete StepsListCrudView (Tkinter) from the Presenter so that
the Presenter remains testable without a display.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from collections.abc import Callable
from typing import Any, Protocol

from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepsListCrudView(Protocol):
    """Callback surface and render contract for the drag-and-drop step list.

    The Presenter sets the callback attributes and calls the render methods.
    The view never imports services or repositories.
    """

    # -- Callback slots set by the Presenter --------------------------------

    on_edit_step: Callable[[int], None] | None
    on_delete_step: Callable[[int], None] | None
    on_move_step: Callable[[int, int], None] | None
    on_toggle_active_step: Callable[[int], None] | None
    on_reorder_steps: Callable[[list[StepScrapingModel]], None] | None
    on_confirm_create_step: Callable[[StepTypeEnum, dict[str, Any]], bool] | None
    on_confirm_update_step: Callable[[StepTypeEnum, dict[str, Any]], bool] | None
    on_cancel_inline_step: Callable[[], None] | None
    on_clear_all_steps: Callable[[], None] | None
    on_duplicate_step: Callable[[StepScrapingModel, int], StepScrapingModel] | None

    # -- Render methods called by the Presenter -----------------------------

    def render_steps(self, steps: list[StepScrapingModel]) -> None:
        """Redraw the entire step list.

        Args:
            steps: Current ordered list of steps to display.
        """
        ...

    def clear_selection(self) -> None:
        """Clear the current step selection and repaint the deselected item."""
        ...

    def set_validation_status(self, message: str, is_error: bool) -> None:
        """Update the workflow validation status label.

        Args:
            message: Status text to display.
            is_error: True for error styling (red); False for success (green).
        """
        ...


# EOF
