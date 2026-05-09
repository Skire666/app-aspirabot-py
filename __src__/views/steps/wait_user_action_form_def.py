"""IStepFormDef for WAIT_USER_ACTION."""

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
from views.steps._constants import (
    CONDITION_DISPLAY,
    CONDITION_MODEL_TO_VIEW,
    CONDITION_VIEW_TO_MODEL,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

from __src__.shared.i18n_fra import C_STEP_TYPE_TO_LABELS

C_INPUT_DEFAULT_POST_WAIT_DURATION: int = 3
C_INPUT_DEFAULT_CONDITION: str = CONDITION_DISPLAY[-1]  # "Toujours"


class WaitUserActionFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_USER_ACTION

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.WAIT_USER_ACTION)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Condition:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        cond_var = tk.StringVar(value=C_INPUT_DEFAULT_CONDITION)
        ttk.Combobox(frame, textvariable=cond_var, values=CONDITION_DISPLAY, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        widgets["condition"] = cond_var

        delay_frame = ttk.Frame(frame)
        delay_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(delay_frame, text="Délai post-reprise :").pack(side=tk.LEFT, padx=(0, 4))
        dur_var = tk.StringVar(value=str(C_INPUT_DEFAULT_POST_WAIT_DURATION))
        ttk.Spinbox(delay_frame, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            delay_frame, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(delay_frame, text="(0 = immédiat)", foreground="gray").pack(side=tk.LEFT)
        widgets["wait_duration"] = dur_var
        widgets["wait_unit"] = unit_var

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["condition"].set(
            CONDITION_MODEL_TO_VIEW.get(model.params.get("condition", "always"), C_INPUT_DEFAULT_CONDITION)
        )
        widgets["wait_duration"].set(str(model.params.get("wait_duration", C_INPUT_DEFAULT_POST_WAIT_DURATION)))
        widgets["wait_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "condition": CONDITION_VIEW_TO_MODEL.get(widgets["condition"].get(), "always"),
            "wait_duration": safe_int_widget(widgets, "wait_duration", C_INPUT_DEFAULT_POST_WAIT_DURATION),
            "wait_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["wait_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if safe_int_widget(widgets, "wait_duration", -1) < 0:
            errors.append("Délai post-reprise : doit être >= 0")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        cond_labels = {"success": "Si succès", "failure": "Si échec", "always": "Toujours"}
        condition = cond_labels.get(model.params.get("condition", "always"), "toujours")
        wd = model.params.get("wait_duration", C_INPUT_DEFAULT_POST_WAIT_DURATION)
        unit_time = model.params.get("wait_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)

        delay_str = f"Si reprise demandée, patienter {wd} {unit_display}" if wd > 0 else ""
        return f"{condition} attendre action utilisateur\n{delay_str}"


register_form(WaitUserActionFormDef())
