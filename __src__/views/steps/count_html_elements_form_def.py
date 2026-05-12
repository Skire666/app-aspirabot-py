"""IStepFormDef for COUNT_ELEMENT."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import (
    C_MAXIMUM_QTY_COUNTER,
)
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_TIME_WAIT = 100

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class CountHtmlElementsFormDef(IStepFormDef):
    """Form definition for the count element scraping step."""

    def __init__(self) -> None:
        """Initialize the form state references."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.COUNT_HTML_ELEMENTS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.COUNT_HTML_ELEMENTS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        self._form_widgets_ref = widgets

        # ROW 1 — CSS selector
        self._build_form_selector_css(frame, widgets)

        # ROW 2 — success_if + operator + value area
        self._build_success_if_operator(frame, widgets)

        # ROW 3 — comment
        self._build_form_comment(frame, widgets)

    def _build_form_selector_css(self, frame, widgets):
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Sélecteur CSS :").pack(side=tk.LEFT, padx=(0, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row1, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["selector"] = sel_var

    def _build_success_if_operator(self, frame, widgets):
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Est un").pack(side=tk.LEFT, padx=(0, 5))
        si_var = tk.StringVar(value=COUNT_SUCCESS_IF_DISPLAY[0])
        ttk.Combobox(row2, textvariable=si_var, values=COUNT_SUCCESS_IF_DISPLAY, state="readonly", width=8).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(row2, text="si compte").pack(side=tk.LEFT, padx=(0, 5))
        widgets["success_if"] = si_var

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[-1])  # supérieur ou égal
        op_cb = ttk.Combobox(row2, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18)
        op_cb.pack(side=tk.LEFT, padx=(0, 5))
        widgets["operator"] = op_var

        val_var = tk.StringVar(value="1")
        ttk.Spinbox(row2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=val_var, width=6).pack(side=tk.LEFT)
        widgets["value"] = val_var

    def _build_form_comment(self, frame, widgets):
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))

        ttk.Label(row3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        # sélecteur CSS
        widgets["selector"].set(model.params.get("selector", C_INPUT_DEFAULT_CSS_SELECTOR))
        si_display = COUNT_SUCCESS_IF_MODEL_TO_VIEW.get(
            model.params.get("success_if", "success"), COUNT_SUCCESS_IF_DISPLAY[0]
        )

        # opérateur et zone de saisie dynamique
        widgets["success_if"].set(si_display)
        op_display = COUNT_OP_MODEL_TO_VIEW.get(model.params.get("operator", "equal"), COUNT_OP_DISPLAY[2])
        widgets["operator"].set(op_display)
        widgets["value"].set(str(model.params.get("value", 0)))

        # commentaire
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        si_display = widgets["success_if"].get()
        op_display = widgets["operator"].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")

        # Valeurs communes à tous les opérateurs
        return {
            "selector": widgets["selector"].get().strip(),
            "success_if": COUNT_SUCCESS_IF_VIEW_TO_MODEL.get(si_display, "success"),
            "operator": op_value,
            "value": safe_int_widget(widgets, "value", -1),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Sélecteur CSS : valeur obligatoire")

        # 1 seule valeur à valider, avec contrainte de non-négativité.
        val = safe_int_widget(widgets, "value", -1)
        if val < 0:
            errors.append("La valeur doit être >= 0.")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        op_labels = {
            "equal": "==",
            "not_equal": "!=",
            "greater_than": ">",
            "less_than": "<",
            "greater_or_equal": ">=",
            "less_or_equal": "<=",
        }
        op = op_labels.get(model.params.get("operator", "equal"), "?")
        selector = model.params.get("selector", "<vide>")
        val_str = str(model.params.get("value", 0))
        return f"Compter les éléments  -  Doit être {op} {val_str}\nSél. : {selector}"


register_form(CountHtmlElementsFormDef())
