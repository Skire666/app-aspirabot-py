"""Contract for step form building and rendering in the view layer.

Each concrete step type owns exactly one implementation of this interface,
named ``<StepName>FormDef``.  It registers itself in the step registry at
import time.  The view orchestrators query the registry and invoke this
contract without knowing any concrete step type by name.

Example:
    >>> form_def = WaitElementFormDef()
    >>> form_def.label()
    'Vérifier les éléments'
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from tkinter import ttk
from typing import Any, Protocol

from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext
from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepFormDef(Protocol):
    """View-layer contract for one step type.

    Covers everything the view orchestrators need: the display label, the form
    builder, param serialisation in both directions, inline validation, and the
    list-item renderer label.

    The ``widgets`` dict is owned by the caller (``StepInlineFormPanel``) and
    is populated by ``build_form``.  All other methods receive the same dict
    to read or write widget variables.

    Example:
        >>> form_def = ConcreteFormDef()
        >>> frame = ttk.Frame()
        >>> widgets: dict[str, Any] = {}
        >>> form_def.build_form(frame, widgets)
        >>> "selector" in widgets
        True
    """

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepTypeEnum this definition handles.

        Returns:
            The matching StepTypeEnum enum member.
        """
        ...

    @classmethod
    def label(cls) -> str:
        """Return the French display label shown in the step type selector.

        Returns:
            A short French label string.
        """
        ...

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Populate ``frame`` with the step-specific form widgets.

        Widget variables are stored in ``widgets`` under their parameter key
        so that ``load_params`` and ``read_params_from_view`` can access them by name.

        Args:
            frame: Empty ttk.Frame to populate.
            widgets: Mutable dict; implementations store tk.Variable instances here.
        """
        ...

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from an existing params dict.

        Called when the user opens an existing step for editing.

        Args:
            model: Step model containing the stored parameters.
            widgets: Dict populated by ``build_form``.
        """
        ...

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return a raw params dict.

        Args:
            widgets: Dict populated by ``build_form``.

        Returns:
            A plain dict suitable for JSON storage.
        """
        ...

    def format_label(self, model: StepScrapingModel, idx: int, steps_context: StepsContext) -> str:
        """Return the renderer label for a step list item.

        Args:
            model: The step model instance.
            idx: Zero-based index of the step in the workflow.
            steps_context: Read-only snapshot of the full workflow; used by
                steps that reference siblings (e.g. JUMP_TO_STEP).

        Returns:
            A short multi-line string for display in the DragDropList.
        """
        ...


# EOF
