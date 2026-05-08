"""IStepFormDef for COUNT_ELEMENT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import (
    C_MAXIMUM_SIZE_IMAGE,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.step_registry import register_form
from views.steps._constants import (
    COUNT_OP_DISPLAY,
    COUNT_OP_MODEL_TO_VIEW,
    COUNT_OP_VIEW_TO_MODEL,
    COUNT_SUCCESS_IF_DISPLAY,
    COUNT_SUCCESS_IF_MODEL_TO_VIEW,
    COUNT_SUCCESS_IF_VIEW_TO_MODEL,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

C_INPUT_DEFAULT_CSS_SELECTOR = "<div class='ds-theme' >> div.ds-theme   ||  id='header' >> #header  ||  ou sinon copy selector dans chrome/debug"
C_INPUT_DEFAULT_TIME_WAIT = 100


class CountElementFormDef(IStepFormDef):
    def __init__(self) -> None:
        self._value_area_frame: ttk.Frame | None = None
        self._form_widgets_ref: dict[str, Any] | None = None

    @classmethod
    def step_type(cls) -> StepType:
        return StepType.COUNT_ELEMENT

    @classmethod
    def label(cls) -> str:
        return "Compter les éléments"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        self._form_widgets_ref = widgets

        # ROW 0 — pre-wait
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=2)

        ttk.Label(row0, text="Attendre avant évaluation : ").pack(side=tk.LEFT, padx=(5, 4))
        wd_var = tk.StringVar(value=C_INPUT_DEFAULT_TIME_WAIT)
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=wd_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        wu_var = tk.StringVar(value=C_UNITS_TIME_ALLOWED_FOR_VIEW[-1])
        ttk.Combobox(
            row0, textvariable=wu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row0, text="(0 = immédiat)").pack(side=tk.LEFT)
        widgets["wait_duration"] = wd_var
        widgets["wait_unit"] = wu_var

        # ROW 1 — CSS selector
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=2)

        ttk.Label(row1, text="Sélecteur CSS : ").pack(side=tk.LEFT, padx=(5, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row1, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["selector"] = sel_var

        # ROW 2 — success_if + operator + dynamic value area
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=4)

        si_var = tk.StringVar(value=COUNT_SUCCESS_IF_DISPLAY[0])
        ttk.Combobox(row2, textvariable=si_var, values=COUNT_SUCCESS_IF_DISPLAY, state="readonly", width=8).pack(
            side=tk.LEFT, padx=(5)
        )
        ttk.Label(row2, text="si").pack(side=tk.LEFT, padx=(5))
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
        if op_value in {"between", "not_between"}:
            vmin_var = tk.StringVar(value="0")
            ttk.Spinbox(
                self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=vmin_var, width=7
            ).pack(side=tk.LEFT, padx=(0, 6))
            ttk.Label(self._value_area_frame, text=" et ").pack(side=tk.LEFT)
            vmax_var = tk.StringVar(value="0")
            ttk.Spinbox(
                self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=vmax_var, width=7
            ).pack(side=tk.LEFT)
            self._form_widgets_ref["value_min"] = vmin_var
            self._form_widgets_ref["value_max"] = vmax_var
        else:
            ttk.Label(self._value_area_frame, text="valeur").pack(side=tk.LEFT, padx=(0, 2))
            val_var = tk.StringVar(value="0")
            ttk.Spinbox(
                self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=val_var, width=7
            ).pack(side=tk.LEFT)
            self._form_widgets_ref["value"] = val_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        self._form_widgets_ref = widgets
        widgets["selector"].set(params.get("selector", C_INPUT_DEFAULT_CSS_SELECTOR))
        widgets["wait_duration"].set(str(params.get("wait_duration", 0)))
        unit_model = params.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL)
        widgets["wait_unit"].set(WAIT_UNIT_MODEL_TO_VIEW.get(unit_model, C_UNITS_TIME_DEFAULT_VIEW))
        si_display = COUNT_SUCCESS_IF_MODEL_TO_VIEW.get(
            params.get("success_if", "success"), COUNT_SUCCESS_IF_DISPLAY[0]
        )
        widgets["success_if"].set(si_display)
        op_display = COUNT_OP_MODEL_TO_VIEW.get(params.get("operator", "equal"), COUNT_OP_DISPLAY[2])
        widgets["operator"].set(op_display)
        self._rebuild_value_area(op_display)
        if "value_min" in widgets:
            widgets["value_min"].set(str(params.get("value_min", 0)))
        if "value_max" in widgets:
            widgets["value_max"].set(str(params.get("value_max", 0)))
        if "value" in widgets:
            widgets["value"].set(str(params.get("value", 0)))

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        unit_display = widgets["wait_unit"].get()
        si_display = widgets["success_if"].get()
        op_display = widgets["operator"].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")
        result = {
            "selector": widgets["selector"].get().strip(),
            "wait_duration": safe_int_widget(widgets, "wait_duration", 0),
            "wait_unit": WAIT_UNIT_VIEW_TO_MODEL.get(unit_display, C_UNITS_TIME_DEFAULT_MODEL),
            "success_if": COUNT_SUCCESS_IF_VIEW_TO_MODEL.get(si_display, "success"),
            "operator": op_value,
        }
        if op_value in {"between", "not_between"}:
            result["value_min"] = safe_int_widget(widgets, "value_min", 0)
            result["value_max"] = safe_int_widget(widgets, "value_max", 0)
            result["value"] = 0
        else:
            result["value_min"] = 0
            result["value_max"] = 0
            result["value"] = safe_int_widget(widgets, "value", 0)
        return result

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if safe_int_widget(widgets, "wait_duration", -1) < 0:
            errors.append("Durée d'attente doit être un nombre positif ou égal à 0.")
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Le sélecteur CSS est obligatoire.")
        op_display = widgets.get("operator", tk.StringVar()).get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")
        if op_value in {"between", "not_between"}:
            if safe_int_widget(widgets, "value_min", 0) > safe_int_widget(widgets, "value_max", 0):
                errors.append("La valeur minimale doit être inférieure ou égale à la valeur maximale.")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        op_labels = {
            "between": "compris entre",
            "equal": "==",
            "not_equal": "!=",
            "greater_than": ">",
            "less_than": "<",
            "greater_or_equal": ">=",
            "less_or_equal": "<=",
        }
        op = op_labels.get(model.params.get("operator", "equal"), "?")
        selector = model.params.get("selector", "<vide>")
        if model.params.get("operator") in {"between", "not_between"}:
            val_str = f"{model.params.get('value_min', 0)} et {model.params.get('value_max', 0)}"
        else:
            val_str = str(model.params.get("value", 0))
        return f"Compter les éléments  -  Attendu {op} {val_str}\nSél. : {selector}"


register_form(CountElementFormDef())
