"""IStepFormDef for WAIT_ELEMENT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import (
    C_MAXIMUM_SIZE_IMAGE,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW


class WaitElementFormDef(IStepFormDef):
    """Form definition for waiting until an element is present."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the StepType handled by this form."""
        return StepType.WAIT_ELEMENTS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.WAIT_ELEMENTS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the selector and timeout widgets into the given frame."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 4))

        ttk.Label(line1, text="Sélecteur CSS : ").pack(side=tk.LEFT, padx=(0, 4))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(line1, textvariable=sel_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        widgets["selector"] = sel_var

        timeout_frame = ttk.Frame(frame)
        timeout_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(timeout_frame, text="Timeout : ").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)
        ttk.Combobox(
            timeout_frame, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load stored parameters into the form widgets."""
        widgets["selector"].set(model.params.get("selector", C_INPUT_DEFAULT_CSS_SELECTOR))
        widgets["timeout_duration"].set(str(model.params.get("timeout_duration", C_INPUT_DEFAULT_TIMEOUT_DURATION)))
        widgets["timeout_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read widget values into a parameters mapping."""
        return {
            "selector": widgets["selector"].get().strip(),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", 0),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate the current form values and return error messages."""
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Sélecteur CSS : valeur obligatoire")
        if safe_int_widget(widgets, "timeout_duration", -1) < 1:
            errors.append("Durée de timeout : doit être >= 1")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact label for the workflow list."""
        selector = model.params.get("selector", "<vide>")

        timeout = model.params.get("timeout_duration", 0)
        unit_time = model.params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)

        return f"Présence d'un élément  -  timeout : {timeout} {unit_display}\nSél. : {selector}"


register_form(WaitElementFormDef())
