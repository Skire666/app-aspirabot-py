"""IStepFormDef for REFRESH_PAGE."""

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
    C_MAXIMUM_WAIT_TIME,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import (
    C_CHOICES_WAIT_PAGE_STATE,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_WAIT_STATE = "load"
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class RefreshPageFormDef(IStepFormDef):
    """Form definition for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.REFRESH_PAGE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.REFRESH_PAGE)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        cache_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row0, text="Vider le cache (Ctrl + F5)", variable=cache_var).pack(side="left", padx=(0, 5))
        widgets["clear_cache"] = cache_var

        self._build_subform_wait_state(frame, widgets)

        # Build timeout controls
        self._build_subform_timeout(frame, widgets)

        # comment
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))
        ttk.Label(row1, text="Commentaire : ").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @staticmethod
    def _build_subform_wait_state(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the wait-state selector."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Attendre le chargement :").pack(side=tk.LEFT, padx=(0, 5))
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(line1, textvariable=ws_var, values=C_CHOICES_WAIT_PAGE_STATE, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line1, text="(dom >load >idle)").pack(side=tk.LEFT, padx=(0, 5))
        widgets["wait_state"] = ws_var

    @staticmethod
    def _build_subform_timeout(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the timeout controls."""
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        # timeout duration
        ttk.Label(line3, text="Timeout : ").pack(side=tk.LEFT, padx=(0, 5))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)

        ttk.Combobox(line3, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["clear_cache"].set(bool(model.params.get("clear_cache", False)))
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
        """Read current widget values and return them as a parameters dict."""
        return {
            "clear_cache": bool(widgets["clear_cache"].get()),
            "wait_state": widgets["wait_state"].get(),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", 0),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validates the form and returns user-facing errors."""
        errors: list[str] = []
        if safe_int_widget(widgets, "timeout_duration", -1) < 1:
            errors.append("Durée de timeout : doit être >= 1")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        mode_clear_cache = "Vide le cache (Ctrl+F5)" if model.params.get("clear_cache") else "Garde le cache (F5)"
        timeout = model.params.get("timeout_duration", 0)
        unit_time = model.params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)

        return (
            f"Rafraîchir la page  -  timeout : {timeout} {unit_display}\n"
            + f"{mode_clear_cache}  -  Attendre : {model.params.get('wait_state', C_INPUT_DEFAULT_WAIT_STATE)}"
        )


register_form(RefreshPageFormDef())
