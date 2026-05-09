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

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Any

from models.step_scraping_model import StepScrapingModel, StepType

## ---------------------------------------------------------------------------
## Interface
## ---------------------------------------------------------------------------


class IStepFormDef(ABC):
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
    @abstractmethod
    def step_type(cls) -> StepType:
        """Returns the StepType this definition handles.

        Returns:
            The matching StepType enum member.

        Raises:
            None.
        """

    @classmethod
    @abstractmethod
    def label(cls) -> str:
        """Returns the French display label shown in the step type selector.

        Returns:
            A short French label string.

        Raises:
            None.
        """

    @abstractmethod
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Populates ``frame`` with the step-specific form widgets.

        Widget variables are stored in ``widgets`` under their parameter key
        so that ``load_params``, ``read_params_from_view``, and ``validate_form`` can
        access them by name.

        Args:
            frame: Empty ttk.Frame to populate.
            widgets: Mutable dict; implementations store tk.Variable instances here.

        Returns:
            None.

        Raises:
            None.
        """

    @abstractmethod
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Pre-fills form widgets from an existing params dict.

        Called when the user opens an existing step for editing.

        Args:
            params: Raw parameter dict from the step model.
            widgets: Dict populated by ``build_form``.

        Returns:
            None.

        Raises:
            None.
        """

    @abstractmethod
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Reads current widget values and returns a raw params dict.

        Args:
            widgets: Dict populated by ``build_form``.

        Returns:
            A plain dict suitable for JSON storage.

        Raises:
            None.
        """

    @abstractmethod
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validates the current form state and returns error messages.

        Args:
            widgets: Dict populated by ``build_form``.

        Returns:
            A list of French error strings; empty when valid.

        Raises:
            None.
        """

    @abstractmethod
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Returns the renderer label for a step list item.

        Args:
            model: The step model instance.
            idx: Zero-based index of the step in the workflow.

        Returns:
            A short multi-line string for display in the DragDropList.

        Raises:
            None.
        """
