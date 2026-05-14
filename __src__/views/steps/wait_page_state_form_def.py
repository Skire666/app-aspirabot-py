"""IStepFormDef for WAIT_PAGE_STATE."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import (
    C_MAXIMUM_WAIT_TIME,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import StepTypeEnum
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

C_INPUT_DEFAULT_MINIMUM_SIZE = 250
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW
C_INPUT_DEFAULT_WAIT_STATE = "load"

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WaitPageStateFormDef(IStepFormDef):
    """Form definition for waiting until a page reaches a certain state.

    Provides widget construction, parameter (de)serialization and validation.
    """

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepType handled by this form definition."""
        return StepTypeEnum.E_WAIT_PAGE_STATE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_PAGE_STATE)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Attendre le chargement :").pack(side=tk.LEFT, padx=(0, 5))
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(line1, textvariable=ws_var, values=C_CHOICES_WAIT_PAGE_STATE, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line1, text="(dom > load > idle 500ms)").pack(side=tk.LEFT, padx=(0, 5))
        widgets["wait_state"] = ws_var

        # Build timeout controls
        self._build_subform_timeout(frame, widgets)

        # Dernière ligne — comment
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @staticmethod
    def _build_subform_timeout(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the timeout controls."""
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        # timeout duration
        ttk.Label(line3, text="Timeout :").pack(side=tk.LEFT, padx=(0, 5))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)

        ttk.Combobox(
            line3, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 5))
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Populate widget values from stored parameters.

        Args:
            model: Step model containing stored parameters.
            widgets: Mapping of form widgets to populate.
        """
        widgets["wait_state"].set(model.params.get("wait_state", C_INPUT_DEFAULT_WAIT_STATE))
        widgets["timeout_duration"].set(
            str(model.params.get("timeout_duration", C_INPUT_DEFAULT_TIMEOUT_DURATION))
        )
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
            "wait_state": widgets["wait_state"].get(),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", -1),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get()),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Produce a compact, human-readable label describing this step instance."""
        timeout = model.params.get("timeout_duration", 0)
        unit_time = model.params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)

        return (
            f"Attendre l'état de chargement  -  timeout : {timeout} {unit_display}\n"
            + f"Attendre : {model.params.get('wait_state', C_INPUT_DEFAULT_WAIT_STATE)}"
        )


register_form(WaitPageStateFormDef())
