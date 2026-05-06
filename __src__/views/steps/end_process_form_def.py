"""IStepFormDef for END_PROCESS."""

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


class EndProcessFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.END_PROCESS

    @classmethod
    def label(cls) -> str:
        return "Fin du processus"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:

        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=4)

        ttk.Label(row0, text="Attendre avant de fermer:").pack(side=tk.LEFT, padx=(5, 5))
        dur_var = tk.StringVar(value="5")
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets["wait_duration"] = dur_var

        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            row0, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        widgets["wait_unit"] = unit_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["wait_duration"].set(str(params.get("wait_duration", 5)))
        widgets["wait_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                params.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "wait_duration": safe_int_widget(widgets, "wait_duration", 0),
            "wait_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["wait_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        return []

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        unit_time = params.get("wait_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Fin du processus\nAttendre {params.get('wait_duration', 0)} {unit_display} avant de quitter"


register_form(EndProcessFormDef())
