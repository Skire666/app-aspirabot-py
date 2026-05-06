"""IStepFormDef for COUNT_ELEMENT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
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


class CountElementFormDef(IStepFormDef):
    def __init__(self) -> None:
        self._value_area_frame: ttk.Frame | None = None
        self._form_widgets_ref: dict[str, Any] | None = None

    @classmethod
    def step_type(cls) -> StepType:
        return StepType.COUNT_ELEMENT

    @classmethod
    def label(cls) -> str:
        return "Dénombrer les éléments"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        self._form_widgets_ref = widgets
        frame.columnconfigure(1, weight=1)

        # Row 0 — pre-wait
        wait_frame = ttk.Frame(frame)
        wait_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(wait_frame, text="Attendre ").pack(side=tk.LEFT, padx=(0, 4))
        wd_var = tk.StringVar(value="0")
        ttk.Spinbox(wait_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=wd_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        wu_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            wait_frame, textvariable=wu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(wait_frame, text=" avant de lancer l'évaluation (0 = immédiat)").pack(side=tk.LEFT)
        widgets["wait_duration"] = wd_var
        widgets["wait_unit"] = wu_var

        # Row 1 — CSS selector
        ttk.Label(frame, text="Sélecteur CSS:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(frame, textvariable=sel_var).grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        widgets["selector"] = sel_var

        # Row 2 — success_if + operator + dynamic value area
        result_frame = ttk.Frame(frame)
        result_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(result_frame, text="Est un").pack(side=tk.LEFT, padx=(0, 4))
        si_var = tk.StringVar(value=COUNT_SUCCESS_IF_DISPLAY[0])
        ttk.Combobox(
            result_frame, textvariable=si_var, values=COUNT_SUCCESS_IF_DISPLAY, state="readonly", width=8
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(result_frame, text="si le résultat est ").pack(side=tk.LEFT, padx=(4, 0))
        widgets["success_if"] = si_var

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[2])
        op_cb = ttk.Combobox(
            result_frame, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18
        )
        op_cb.pack(side=tk.LEFT, padx=(0, 6))
        widgets["operator"] = op_var

        self._value_area_frame = ttk.Frame(result_frame)
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
            ttk.Label(self._value_area_frame, text="min").pack(side=tk.LEFT, padx=(0, 2))
            vmin_var = tk.StringVar(value="0")
            ttk.Spinbox(
                self._value_area_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=vmin_var, width=7
            ).pack(side=tk.LEFT, padx=(0, 6))
            ttk.Label(self._value_area_frame, text="max").pack(side=tk.LEFT, padx=(0, 2))
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
        widgets["selector"].set(params.get("selector", ""))
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

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
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

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        op_labels = {
            "between": "compris entre",
            "not_between": "non compris entre",
            "equal": "==",
            "not_equal": "!=",
            "greater_than": ">",
            "less_than": "<",
            "greater_or_equal": ">=",
            "less_or_equal": "<=",
        }
        op = op_labels.get(params.get("operator", "equal"), "?")
        selector = params.get("selector", "")
        if params.get("operator") in {"between", "not_between"}:
            val_str = f"{params.get('value_min', 0)} et {params.get('value_max', 0)}"
        else:
            val_str = str(params.get("value", 0))
        return f"Dénombrer les éléments\nSél. : '{selector}'  -  Attendu {op} {val_str}"


register_form(CountElementFormDef())
