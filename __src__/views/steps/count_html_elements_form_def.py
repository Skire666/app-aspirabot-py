"""IStepFormDef for COUNT_ELEMENT."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import (
    C_MAXIMUM_QTY_COUNTER,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    COUNT_OP_DISPLAY,
    COUNT_OP_MODEL_TO_VIEW,
    COUNT_OP_VIEW_TO_MODEL,
    COUNT_SUCCESS_IF_DISPLAY,
    COUNT_SUCCESS_IF_MODEL_TO_VIEW,
    COUNT_SUCCESS_IF_VIEW_TO_MODEL,
    safe_int_widget,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_TIME_WAIT = 100

C_KEY_SELECTOR = "selector"
C_KEY_SUCCESS_IF = "success_if"
C_KEY_OPERATOR = "operator"
C_KEY_VALUE = "value"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CountHtmlElementsFormDef(IStepFormDef):
    """Form definition for the count element scraping step."""

    def __init__(self) -> None:
        """Initialize the form state references."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_ELEMENTS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_COUNT_HTML_ELEMENTS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_selector(frame, widgets)
        self._build_subform_success_if_operator(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_selector(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the CSS selector input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_SELECTOR tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Sélecteur CSS :").pack(side=tk.LEFT, padx=(0, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row1, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_SELECTOR] = sel_var

    @staticmethod
    def _build_subform_success_if_operator(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the success condition, comparison operator, and threshold spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_SUCCESS_IF, C_KEY_OPERATOR,
                and C_KEY_VALUE tk.Variables.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Est un").pack(side=tk.LEFT, padx=(0, 5))
        si_var = tk.StringVar(value=COUNT_SUCCESS_IF_DISPLAY[0])
        ttk.Combobox(row2, textvariable=si_var, values=COUNT_SUCCESS_IF_DISPLAY, state="readonly", width=8).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(row2, text="si compte").pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_SUCCESS_IF] = si_var

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[-1])
        ttk.Combobox(row2, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_OPERATOR] = op_var

        val_var = tk.StringVar(value="1")
        ttk.Spinbox(row2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=val_var, width=6).pack(side=tk.LEFT)
        widgets[C_KEY_VALUE] = val_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))

        ttk.Label(row3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_SELECTOR].set(model.params.get(C_KEY_SELECTOR, C_INPUT_DEFAULT_CSS_SELECTOR))
        si_display = COUNT_SUCCESS_IF_MODEL_TO_VIEW.get(
            model.params.get(C_KEY_SUCCESS_IF, "success"), COUNT_SUCCESS_IF_DISPLAY[0]
        )
        widgets[C_KEY_SUCCESS_IF].set(si_display)

        op_display = COUNT_OP_MODEL_TO_VIEW.get(model.params.get(C_KEY_OPERATOR, "equal"), COUNT_OP_DISPLAY[-1])
        widgets[C_KEY_OPERATOR].set(op_display)
        widgets[C_KEY_VALUE].set(str(model.params.get(C_KEY_VALUE, 0)))
        widgets[C_KEY_COMMENT].set(model.params.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        si_display = widgets[C_KEY_SUCCESS_IF].get()
        op_display = widgets[C_KEY_OPERATOR].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")

        return {
            C_KEY_SELECTOR: widgets[C_KEY_SELECTOR].get().strip(),
            C_KEY_SUCCESS_IF: COUNT_SUCCESS_IF_VIEW_TO_MODEL.get(si_display),
            C_KEY_OPERATOR: op_value,
            C_KEY_VALUE: safe_int_widget(widgets, C_KEY_VALUE, -1),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        op_labels = {
            "equal": "==",
            "not_equal": "!=",
            "greater_than": ">",
            "less_than": "<",
            "greater_or_equal": ">=",
            "less_or_equal": "<=",
        }
        op = op_labels.get(model.params.get(C_KEY_OPERATOR, "equal"), "?")
        selector = model.params.get(C_KEY_SELECTOR, "<vide>")
        val_str = str(model.params.get(C_KEY_VALUE, 0))
        return f"Compter les éléments  -  Doit être {op} {val_str}\nSél. : {selector}"


register_form(CountHtmlElementsFormDef())

# EOF
