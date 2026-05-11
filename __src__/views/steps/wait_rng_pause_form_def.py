"""IStepFormDef for RANDOM_PAUSE."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

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

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WaitRandomPauseFormDef(IStepFormDef):
    """Form definition for the random pause scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_RANDOM_PAUSE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.WAIT_RANDOM_PAUSE)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        min_var = tk.StringVar(value="500")
        max_var = tk.StringVar(value="1000")
        unit_var = tk.StringVar(value="millisec")
        widgets["min"] = min_var
        widgets["max"] = max_var
        widgets["unit"] = unit_var

        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        # line for min and max values
        ttk.Label(line1, text="Pause aléatoire entre : ").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=min_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line1, text=" et ").pack(side=tk.LEFT)
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=max_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Combobox(
            line1, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT)

        # ROW 2 — comment
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Commentaire : ").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["min"].set(str(model.params.get("min", 0)))
        widgets["max"].set(str(model.params.get("max", 1)))
        widgets["unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(model.params.get("unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW)
        )
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "min": safe_int_widget(widgets, "min", 0),
            "max": safe_int_widget(widgets, "max", 1),
            "unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        min_val = safe_int_widget(widgets, "min", -1)
        max_val = safe_int_widget(widgets, "max", -1)

        if min_val < 0:
            errors.append("Valeur min. : doit être >= 0")
        if max_val <= 0:
            errors.append("Valeur max. : doit être >= 1")
        if min_val > max_val:
            errors.append("La valeur min. doit être <= à valeur max.")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        unit_time = model.params.get("unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return (
            f"Attendre aléatoirement\nEntre {model.params.get('min', 0)} et {model.params.get('max', 1)} {unit_display}"
        )


register_form(WaitRandomPauseFormDef())
