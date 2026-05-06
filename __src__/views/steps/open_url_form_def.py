"""IStepFormDef implementation for the OPEN_URL step."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

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
        timeout_frame = ttk.Frame(frame)
        timeout_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=4)

        # timeout duration
        ttk.Label(timeout_frame, text="Timeout").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)

        ttk.Combobox(
            timeout_frame, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(timeout_frame, text="(0 = désactivé)", foreground="gray").pack(side=tk.LEFT)
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    def _build_subform_wait_state(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the wait-state selector."""
        ttk.Label(frame, text="L'état à attendre :").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(frame, textvariable=ws_var, values=WAIT_STATES, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        ttk.Label(frame, text="(dom >load >idle)").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        widgets["wait_state"] = ws_var

    def _build_subform_url(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the URL input field."""
        ttk.Label(frame, text="URL:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        url_var = tk.StringVar(value=C_INPUT_DEFAULT_URL)
        ttk.Entry(frame, textvariable=url_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
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

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
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

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        """Formats the label displayed in the workflow list."""
        url = params.get("url", "")
        td = params.get("timeout_duration", 0)
        unit_time = params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Ouvrir une URL  -  timeout : {td} {unit_display}\nUrl: '{url}'"


register_form(OpenUrlFormDef())
