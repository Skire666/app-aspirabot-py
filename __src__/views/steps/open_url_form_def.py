"""IStepFormDef implementation for the OPEN_URL step."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

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
from views.steps._constants import WAIT_STATES, WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

C_INPUT_DEFAULT_URL = "https://example.com/"
C_INPUT_DEFAULT_WAIT_STATE = "load"
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class OpenUrlFormDef(IStepFormDef):
    """Builds the Open URL step form and handles its validation."""

    @classmethod
    def step_type(cls) -> StepType:
        """Returns the workflow step handled by this form definition."""
        return StepType.OPEN_URL

    @classmethod
    def label(cls) -> str:
        """Returns the label shown in the step picker."""
        return "Ouvrir une URL"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates all widgets used by the Open URL form."""
        frame.columnconfigure(1, weight=1)

        # URL input.
        self._build_subform_url(frame, widgets)

        # Wait state selection.
        self._build_subform_wait_state(frame, widgets)

        # timeout configuration + units.
        self._build_subform_timeout(frame, widgets)

    def _build_subform_timeout(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the timeout controls."""
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=4)

        # timeout duration
        ttk.Label(line3, text="Timeout : ").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)

        ttk.Combobox(
            line3, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    def _build_subform_wait_state(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the wait-state selector."""
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=2)

        ttk.Label(line2, text="L'état à attendre :").pack(side=tk.LEFT, padx=(0, 4))
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(line2, textvariable=ws_var, values=WAIT_STATES, state="readonly").pack(
            side=tk.LEFT, padx=5, pady=4
        )
        ttk.Label(line2, text="(dom >load >idle)").pack(side=tk.LEFT, padx=(0, 4))
        widgets["wait_state"] = ws_var

    def _build_subform_url(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the URL input field."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=2)

        ttk.Label(line1, text="URL : ").pack(side=tk.LEFT, padx=(0, 4))
        url_var = tk.StringVar(value=C_INPUT_DEFAULT_URL)
        ttk.Entry(line1, textvariable=url_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["url"] = url_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Loads persisted parameters into the widgets."""
        widgets["url"].set(params.get("url", C_INPUT_DEFAULT_URL))
        widgets["wait_state"].set(params.get("wait_state", C_INPUT_DEFAULT_WAIT_STATE))
        widgets["timeout_duration"].set(str(params.get("timeout_duration", C_INPUT_DEFAULT_TIMEOUT_DURATION)))
        widgets["timeout_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                params.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Reads the current widget values as step parameters."""
        return {
            "url": widgets["url"].get().strip(),
            "wait_state": widgets["wait_state"].get(),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", 0),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validates the form and returns user-facing errors."""
        errors: list[str] = []
        if not widgets.get("url", tk.StringVar()).get().strip():
            errors.append("L'URL est obligatoire.")
        if safe_int_widget(widgets, "timeout_duration", -1) < 1:
            errors.append("Durée de timeout doit être un nombre supérieur ou égal à 1.")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Formats the label displayed in the workflow list."""
        url = model.params.get("url", "")
        td = model.params.get("timeout_duration", 0)
        unit_time = model.params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Ouvrir une URL  -  timeout : {td} {unit_display}\nUrl: '{url}'"


register_form(OpenUrlFormDef())
