"""IStepFormDef for WAIT_X_TIME."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.constants import (
    C_MAXIMUM_WAIT_TIME,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget

C_INPUT_DEFAULT_DURATION = 3


class WaitXTimeFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.WAIT_X_TIME

    @classmethod
    def label(cls) -> str:
        return "Attendre une durée fixe"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:

        timeout_frame = ttk.Frame(frame)
        timeout_frame.pack(fill="x", pady=4)

        ttk.Label(timeout_frame, text="Attendre une durée de : ").pack(side=tk.LEFT, padx=5, pady=4)
        dur_var = tk.StringVar(value=str(C_INPUT_DEFAULT_DURATION))
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5), pady=4
        )
        widgets["duration"] = dur_var

        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            timeout_frame, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT, padx=(0, 4))
        widgets["unit"] = unit_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["duration"].set(str(params.get("duration", C_INPUT_DEFAULT_DURATION)))
        widgets["unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(params.get("unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW)
        )

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "duration": safe_int_widget(widgets, "duration", C_INPUT_DEFAULT_DURATION),
            "unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if safe_int_widget(widgets, "duration", -1) < 0:
            errors.append("La durée doit être un nombre positif ou égal à 0.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        unit_time = params.get("unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Attendre une durée fixe\n{params.get('duration', C_INPUT_DEFAULT_DURATION)} {unit_display}"


register_form(WaitXTimeFormDef())
