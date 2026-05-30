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

from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IStepFormDef(Protocol):
    """View-layer contract for one step type.

    Covers everything the view orchestrators need: the display label, the form
    builder, and param serialisation in both directions.

    The ``widgets`` dict is owned by the caller (``StepInlineFormPanel``) and
    is populated by ``build_form``.  All other methods receive the same dict
    to read or write widget variables.

    ``load_params_step_to_widget`` receives a plain ``params_dict``
    (from ``IStepParams.to_dict()``) so that no domain model ever crosses the
    view boundary.

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

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Populate ``frame`` with the step-specific form widgets.

        Widget variables are stored in ``widgets`` under their parameter key
        so that ``load_params_step_to_widget`` and ``read_params_from_view``
        can access them by name.

        Args:
            frame: Empty ttk.Frame to populate.
            widgets: Mutable dict; implementations store tk.Variable instances here.
        """
        ...

    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Called when the user opens an existing step for editing.  Receives a
        plain dict (``IStepParams.to_dict()``) instead of a domain model so
        that form-def implementations never import from ``models/``.

        Args:
            params_dict: Serialised step parameters keyed by field name.
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


# EOF
