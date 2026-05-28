"""IStepFormDef for WAIT_HTML_ELEMENTS."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import (
    C_MAXIMUM_QTY_COUNTER,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    COUNT_OP_DISPLAY,
    COUNT_OP_MODEL_TO_VIEW,
    COUNT_OP_VIEW_TO_MODEL,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_RETRY_UNIT = C_UNITS_TIME_ALLOWED_FOR_VIEW[-1]  # ms
C_INPUT_DEFAULT_RETRY_DELAY = 400

C_KEY_SELECTOR = "selector"
C_KEY_OPERATOR = "operator"
C_KEY_QUANTITY_EXPECTED = "quantity"
C_KEY_RETRY_DELAY = "retry_delay"
C_KEY_RETRY_UNIT = "retry_unit"
C_KEY_RETRY_MAX = "retry_max"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WaitHtmlElementsFormDef(IStepFormDef):
    """Form definition for waiting until an element is present."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepTypeEnum handled by this form."""
        return StepTypeEnum.E_WAIT_HTML_ELEMENTS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_HTML_ELEMENTS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_selector(frame, widgets)
        self._build_subform_waiting_elements(frame, widgets)
        self._build_subform_retry_delay(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_selector(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the CSS selector input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_SELECTOR tk.Variable.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Sélecteur CSS :").pack(side=tk.LEFT, padx=(0, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(line1, textvariable=sel_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        widgets[C_KEY_SELECTOR] = sel_var

    @staticmethod
    def _build_subform_waiting_elements(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the element count operator and quantity spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_OPERATOR and C_KEY_QUANTITY_EXPECTED tk.Variables.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Attendre un nombre").pack(side=tk.LEFT, padx=(0, 5))

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[-1])
        ttk.Combobox(row2, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_OPERATOR] = op_var

        val_var = tk.StringVar(value="1")
        ttk.Spinbox(row2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=val_var, width=6).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_QUANTITY_EXPECTED] = val_var
        ttk.Label(row2, text="d'élément(s)").pack(side=tk.LEFT, padx=(0, 5))

    @staticmethod
    def _build_subform_retry_delay(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the retry interval spinbox, time unit combobox, and max attempts spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_RETRY_DELAY, C_KEY_RETRY_UNIT,
                and C_KEY_RETRY_MAX tk.Variables.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Toutes les").pack(side=tk.LEFT, padx=(0, 5))
        every_var = tk.StringVar(value=str(C_INPUT_DEFAULT_RETRY_DELAY))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=every_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        unit_var = tk.StringVar(value=C_INPUT_DEFAULT_RETRY_UNIT)
        ttk.Combobox(
            line2, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(line2, text="avec").pack(side=tk.LEFT, padx=(0, 5))
        max_var = tk.StringVar(value="10")
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=max_var, width=6).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line2, text="essai(s) max.").pack(side=tk.LEFT)

        widgets[C_KEY_RETRY_DELAY] = every_var
        widgets[C_KEY_RETRY_UNIT] = unit_var
        widgets[C_KEY_RETRY_MAX] = max_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_SELECTOR].set(model.params.get(C_KEY_SELECTOR, C_INPUT_DEFAULT_CSS_SELECTOR))

        op_display = COUNT_OP_MODEL_TO_VIEW.get(model.params.get(C_KEY_OPERATOR, "equal"), COUNT_OP_DISPLAY[-1])
        widgets[C_KEY_OPERATOR].set(op_display)
        widgets[C_KEY_QUANTITY_EXPECTED].set(str(model.params.get(C_KEY_QUANTITY_EXPECTED, 1)))
        widgets[C_KEY_RETRY_DELAY].set(str(model.params.get(C_KEY_RETRY_DELAY, C_INPUT_DEFAULT_RETRY_DELAY)))
        widgets[C_KEY_RETRY_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get(C_KEY_RETRY_UNIT, C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )
        widgets[C_KEY_RETRY_MAX].set(str(model.params.get(C_KEY_RETRY_MAX, 10)))
        widgets[C_KEY_COMMENT].set(model.params.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        op_display = widgets[C_KEY_OPERATOR].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")

        return {
            C_KEY_SELECTOR: widgets[C_KEY_SELECTOR].get().strip(),
            C_KEY_OPERATOR: op_value,
            C_KEY_QUANTITY_EXPECTED: safe_int_widget(widgets, C_KEY_QUANTITY_EXPECTED, -1),
            C_KEY_RETRY_DELAY: safe_int_widget(widgets, C_KEY_RETRY_DELAY, -1),
            C_KEY_RETRY_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_RETRY_UNIT].get()),
            C_KEY_RETRY_MAX: safe_int_widget(widgets, C_KEY_RETRY_MAX, -1),
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
        quantity = model.params.get(C_KEY_QUANTITY_EXPECTED)
        selector = model.params.get(C_KEY_SELECTOR)

        return f"Attendre éléments  -  Attendu {op} {quantity}\nSél. : {selector}"


register_form(WaitHtmlElementsFormDef())
