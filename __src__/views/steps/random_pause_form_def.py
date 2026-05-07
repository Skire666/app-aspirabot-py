"""IStepFormDef for RANDOM_PAUSE."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import (
    C_MAXIMUM_WAIT_TIME,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget


class RandomPauseFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.RANDOM_PAUSE

    @classmethod
    def label(cls) -> str:
        return "Attendre aléatoirement"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        min_var = tk.StringVar(value="500")
        max_var = tk.StringVar(value="1000")
        unit_var = tk.StringVar(value="millisec")
        widgets["min"] = min_var
        widgets["max"] = max_var
        widgets["unit"] = unit_var

        # To make the second column expand and keep the form compact on the left.
        frame.columnconfigure(1, weight=1)

        # line for min and max values
        row0 = ttk.Frame(frame)
        row0.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(row0, text="Pause aléatoire entre : ").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=min_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Label(row0, text=" et ").pack(side=tk.LEFT)
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=max_var, width=7).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Combobox(
            row0, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT)

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["min"].set(str(params.get("min", 0)))
        widgets["max"].set(str(params.get("max", 1)))
        widgets["unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(params.get("unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW)
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "min": safe_int_widget(widgets, "min", 0),
            "max": safe_int_widget(widgets, "max", 1),
            "unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        min_val = safe_int_widget(widgets, "min", 0)
        max_val = safe_int_widget(widgets, "max", 1)
        if min_val >= max_val:
            errors.append("La valeur minimale doit être strictement inférieure à la valeur maximale.")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        unit_time = model.params.get("unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Attendre aléatoirement\nEntre {model.params.get('min', 0)} et {model.params.get('max', 1)} {unit_display}"


register_form(RandomPauseFormDef())
