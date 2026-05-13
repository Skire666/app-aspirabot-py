"""IStepFormDef implementation for the OPEN_URL step."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

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
from views.steps._constants import (
    C_CHOICES_WAIT_PAGE_STATE,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_URL = "https://example.com/"
C_INPUT_DEFAULT_WAIT_STATE = "load"
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class OpenUrlFormDef(IStepFormDef):
    """Builds the Open URL step form and handles its validation."""

    @classmethod
    def step_type(cls) -> StepType:
        """Returns the workflow step handled by this form definition."""
        return StepType.OPEN_URL

    @classmethod
    def label(cls) -> str:
        """Returns the label shown in the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.OPEN_URL)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates all widgets used by the Open URL form."""
        frame.columnconfigure(1, weight=1)

        # URL input.
        self._build_subform_url(frame, widgets)

        # Wait state selection.
        self._build_subform_wait_state(frame, widgets)

        # timeout configuration + units.
        self._build_subform_timeout(frame, widgets)

        # Comment.
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_url(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the URL input field."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        url_mode_var = tk.StringVar(value="<<URL>>")
        url_custom_var = tk.StringVar(value=C_INPUT_DEFAULT_URL)

        # Radiobutton 1
        tk.Radiobutton(
            line1,
            text="Consommer la prochaine URL",
            variable=url_mode_var,
            value="<<URL>>",
        ).pack(side=tk.LEFT, padx=(0, 20))

        # Radiobutton 2
        tk.Radiobutton(
            line1,
            text="URL personnalisée",
            variable=url_mode_var,
            value="<<CUSTOM>>",
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Entry(line1, textvariable=url_custom_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["url_mode"] = url_mode_var
        widgets["url_custom"] = url_custom_var

    @staticmethod
    def _build_subform_wait_state(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the wait-state selector."""
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Attendre le chargement :").pack(side=tk.LEFT, padx=(0, 5))
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(line2, textvariable=ws_var, values=C_CHOICES_WAIT_PAGE_STATE, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line2, text="(dom > load > idle 500ms)").pack(side=tk.LEFT, padx=(0, 5))
        widgets["wait_state"] = ws_var

    @staticmethod
    def _build_subform_timeout(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the timeout controls."""
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        # timeout duration
        ttk.Label(line3, text="Timeout :").pack(side=tk.LEFT, padx=(0, 5))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)

        ttk.Combobox(line3, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the comment input field."""
        line4 = ttk.Frame(frame)
        line4.pack(fill="x", pady=(0, 8))

        ttk.Label(line4, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line4, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Loads persisted parameters into the widgets."""
        widgets["url_mode"].set(model.params.get("url_mode", "<<URL>>"))
        widgets["url_custom"].set(model.params.get("url_custom", C_INPUT_DEFAULT_URL))
        widgets["wait_state"].set(model.params.get("wait_state", C_INPUT_DEFAULT_WAIT_STATE))
        widgets["timeout_duration"].set(str(model.params.get("timeout_duration", C_INPUT_DEFAULT_TIMEOUT_DURATION)))
        widgets["timeout_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Reads the current widget values as step parameters."""
        return {
            "url_mode": widgets["url_mode"].get(),
            "url_custom": widgets["url_custom"].get().strip(),
            "wait_state": widgets["wait_state"].get(),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", 1),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validates the form and returns user-facing errors."""
        errors: list[str] = []
        if safe_int_widget(widgets, "timeout_duration", -1) <= 0:
            errors.append("Durée de timeout : doit être >= 1")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Formats the label displayed in the workflow list."""
        timeout = model.params.get("timeout_duration", 0)
        unit_time = model.params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Ouvrir une URL  -  timeout : {timeout} {unit_display}\nUrl: 'TODO PCO'"


register_form(OpenUrlFormDef())
