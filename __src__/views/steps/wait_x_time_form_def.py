"""IStepFormDef for WAIT_X_TIME."""

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
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget

C_INPUT_DEFAULT_DURATION = 3


class WaitXTimeFormDef(IStepFormDef):
    """Form definition for the wait X time scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_X_TIME

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.WAIT_X_TIME)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        timeout_frame = ttk.Frame(frame)
        timeout_frame.pack(fill="x", pady=(0, 4))

        ttk.Label(timeout_frame, text="Attendre une durée de : ").pack(side=tk.LEFT, padx=(0, 4), pady=(0, 4))
        dur_var = tk.StringVar(value=str(C_INPUT_DEFAULT_DURATION))
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        widgets["duration"] = dur_var

        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            timeout_frame, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT, padx=(0, 4))
        widgets["unit"] = unit_var

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["duration"].set(str(model.params.get("duration", C_INPUT_DEFAULT_DURATION)))
        widgets["unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(model.params.get("unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW)
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "duration": safe_int_widget(widgets, "duration", C_INPUT_DEFAULT_DURATION),
            "unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if safe_int_widget(widgets, "duration", -1) <= 0:
            errors.append("Durée d'attente : doit être >= 1")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        unit_time = model.params.get("unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Attendre une durée fixe\n{model.params.get('duration', C_INPUT_DEFAULT_DURATION)} {unit_display}"


register_form(WaitXTimeFormDef())
