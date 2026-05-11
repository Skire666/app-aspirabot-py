"""IStepFormDef for COUNT_ELEMENT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import (
    C_MAXIMUM_SIZE_IMAGE,
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

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_TIME_WAIT = 100


class CountHtmlElementsFormDef(IStepFormDef):
    """Form definition for the count element scraping step."""

    def __init__(self) -> None:
        """Initialize the form state references."""
        self._value_area_frame: ttk.Frame | None = None
        self._form_widgets_ref: dict[str, Any] | None = None

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
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 4))

        ttk.Label(row1, text="Sélecteur CSS : ").pack(side=tk.LEFT, padx=(0, 4))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row1, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 4))
        widgets["selector"] = sel_var

        # ROW 2 — success_if + operator + dynamic value area
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 4))

        si_var = tk.StringVar(value=COUNT_SUCCESS_IF_DISPLAY[0])
        ttk.Combobox(row2, textvariable=si_var, values=COUNT_SUCCESS_IF_DISPLAY, state="readonly", width=8).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Label(row2, text="si").pack(side=tk.LEFT, padx=(0, 4))
        widgets["success_if"] = si_var

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[-1])  # supérieur ou égal
        op_cb = ttk.Combobox(row2, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18)
        op_cb.pack(side=tk.LEFT, padx=(0, 6))
        widgets["operator"] = op_var

        self._value_area_frame = ttk.Frame(row2)
        self._value_area_frame.pack(side=tk.LEFT)
        self._rebuild_value_area(COUNT_OP_DISPLAY[2])
        op_cb.bind("<<ComboboxSelected>>", lambda _: self._rebuild_value_area(op_var.get()))

    def _rebuild_value_area(self, op_display: str) -> None:
        if self._value_area_frame is None or self._form_widgets_ref is None:
            return
        for w in self._value_area_frame.winfo_children():
            w.destroy()
        for key in ("value", "value_min", "value_max"):
            self._form_widgets_ref.pop(key, None)
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")
        if op_value in {"between"}:
            vmin_var = tk.StringVar(value="0")
            ttk.Spinbox(self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=vmin_var, width=7).pack(
                side=tk.LEFT, padx=(0, 6)
            )
            ttk.Label(self._value_area_frame, text=" et ").pack(side=tk.LEFT)
            vmax_var = tk.StringVar(value="0")
            ttk.Spinbox(self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=vmax_var, width=7).pack(
                side=tk.LEFT, padx=(0, 4)
            )
            self._form_widgets_ref["value_min"] = vmin_var
            self._form_widgets_ref["value_max"] = vmax_var
        else:
            ttk.Label(self._value_area_frame, text="valeur").pack(side=tk.LEFT, padx=(0, 2))
            val_var = tk.StringVar(value="0")
            ttk.Spinbox(self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=val_var, width=7).pack(
                side=tk.LEFT
            )
            self._form_widgets_ref["value"] = val_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        self._form_widgets_ref = widgets
        widgets["selector"].set(model.params.get("selector", C_INPUT_DEFAULT_CSS_SELECTOR))
        si_display = COUNT_SUCCESS_IF_MODEL_TO_VIEW.get(
            model.params.get("success_if", "success"), COUNT_SUCCESS_IF_DISPLAY[0]
        )
        widgets["success_if"].set(si_display)
        op_display = COUNT_OP_MODEL_TO_VIEW.get(model.params.get("operator", "equal"), COUNT_OP_DISPLAY[2])
        widgets["operator"].set(op_display)
        self._rebuild_value_area(op_display)
        if "value_min" in widgets:
            widgets["value_min"].set(str(model.params.get("value_min", 0)))
        if "value_max" in widgets:
            widgets["value_max"].set(str(model.params.get("value_max", 0)))
        if "value" in widgets:
            widgets["value"].set(str(model.params.get("value", 0)))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        si_display = widgets["success_if"].get()
        op_display = widgets["operator"].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")
        result = {
            "selector": widgets["selector"].get().strip(),
            "success_if": COUNT_SUCCESS_IF_VIEW_TO_MODEL.get(si_display, "success"),
            "operator": op_value,
        }
        if op_value in {"between"}:
            result["value_min"] = safe_int_widget(widgets, "value_min", 0)
            result["value_max"] = safe_int_widget(widgets, "value_max", 0)
            result["value"] = 0
        else:
            result["value_min"] = 0
            result["value_max"] = 0
            result["value"] = safe_int_widget(widgets, "value", -1)
        return result

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Sélecteur CSS : valeur obligatoire")

        # Validate operator-specific value constraints.
        op_display = widgets.get("operator", tk.StringVar()).get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")
        if op_value in {"between"}:
            # 2 valeurs à valider : min et max, avec contraintes de non-négativité et de min <= max.
            val_min = safe_int_widget(widgets, "value_min", 0)
            val_max = safe_int_widget(widgets, "value_max", 0)
            if not (val_min <= val_max):
                errors.append("Valeur min. doit être <= à valeur max.")
        else:
            # 1 seule valeur à valider, avec contrainte de non-négativité.
            val = safe_int_widget(widgets, "value", -1)
            if val < 0:
                errors.append("La valeur doit être >= 0.")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        op_labels = {
            "between": "entre",
            "equal": "==",
            "not_equal": "!=",
            "greater_than": ">",
            "less_than": "<",
            "greater_or_equal": ">=",
            "less_or_equal": "<=",
        }
        op = op_labels.get(model.params.get("operator", "equal"), "?")
        selector = model.params.get("selector", "<vide>")
        if model.params.get("operator") in {"between"}:
            val_str = f"{model.params.get('value_min', 0)} et {model.params.get('value_max', 0)}"
        else:
            val_str = str(model.params.get("value", 0))
        return f"Compter les éléments  -  Attendu {op} {val_str}\nSél. : {selector}"


register_form(CountHtmlElementsFormDef())
