"""IStepFormDef for COUNT_HTML_IMAGES."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_MAXIMUM_QTY_COUNTER, C_MAXIMUM_SIZE_IMAGE
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

C_INPUT_DEFAULT_MINIMUM_SIZE = 250

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class CountHtmlImagesFormDef(IStepFormDef):
    """Form definition for the count image scraping step."""

    def __init__(self) -> None:
        """Initialize the form state references."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.COUNT_HTML_IMAGES

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.COUNT_HTML_IMAGES)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        self._form_widgets_ref = widgets

        # ROW 1 — CSS selector
        self._build_subform_width_height(frame, widgets)

        # ROW 2 — success_if + operator + value area
        self._build_success_if_operator(frame, widgets)

        # ROW 3 — comment
        self._build_form_comment(frame, widgets)

    def _build_subform_width_height(self, frame, widgets):
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Largeur entre").pack(side="left", padx=(0, 5))
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=5).pack(side="left")
        ttk.Label(line1, text=" et ").pack(side="left")
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=6).pack(side="left")
        widgets["width_min"] = width_min_var
        widgets["width_max"] = width_max_var

        ttk.Label(line1, text="Hauteur entre").pack(side="left", padx=(24, 5))
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=5).pack(side="left")
        ttk.Label(line1, text=" et ").pack(side="left")
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=6).pack(side="left")
        widgets["height_min"] = height_min_var
        widgets["height_max"] = height_max_var

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
        self._form_widgets_ref = widgets
        widgets["width_min"].set(str(model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["width_max"].set(str(model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["height_min"].set(str(model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["height_max"].set(str(model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))

        si_display = COUNT_SUCCESS_IF_MODEL_TO_VIEW.get(
            model.params.get("success_if", "success"), COUNT_SUCCESS_IF_DISPLAY[0]
        )
        widgets["success_if"].set(si_display)
        op_display = COUNT_OP_MODEL_TO_VIEW.get(model.params.get("operator", "equal"), COUNT_OP_DISPLAY[2])
        widgets["operator"].set(op_display)
        widgets["value"].set(str(model.params.get("value", 0)))

        # comment
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        si_display = widgets["success_if"].get()
        op_display = widgets["operator"].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")
        result = {
            "height_min": safe_int_widget(widgets, "height_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "height_max": safe_int_widget(widgets, "height_max", C_MAXIMUM_SIZE_IMAGE),
            "width_min": safe_int_widget(widgets, "width_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "width_max": safe_int_widget(widgets, "width_max", C_MAXIMUM_SIZE_IMAGE),
            "success_if": COUNT_SUCCESS_IF_VIEW_TO_MODEL.get(si_display, "success"),
            "operator": op_value,
            "comment": widgets["comment"].get().strip(),
        }
        result["value"] = safe_int_widget(widgets, "value", -1)
        return result

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []

        v_height_min = safe_int_widget(widgets, "height_min", -1)
        v_height_max = safe_int_widget(widgets, "height_max", -1)
        v_width_min = safe_int_widget(widgets, "width_min", -1)
        v_width_max = safe_int_widget(widgets, "width_max", -1)

        # Validate non-negativity.
        if v_height_min < 0:
            errors.append("Hauteur min. doit être >= 0.")
        if v_height_max < 1:
            errors.append("Hauteur max. doit être >= 1.")
        if v_width_min < 0:
            errors.append("Largeur min. doit être >= 0.")
        if v_width_max < 1:
            errors.append("Largeur max. doit être >= 1.")

        # Validate min <= max constraints.
        if v_height_min > v_height_max:
            errors.append("Hauteur min. doit être <= hauteur max.")
        if v_width_min > v_width_max:
            errors.append("Largeur min. doit être <= largeur max.")

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
        val_str = str(model.params.get("value", 0))

        width_min = model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        height_min = model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        width_max = model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
        height_max = model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)

        return f"Compter les images  -  Doit être {op} {val_str}\nTaille : {width_min}x{height_min} -> {width_max}x{height_max}"


register_form(CountHtmlImagesFormDef())
