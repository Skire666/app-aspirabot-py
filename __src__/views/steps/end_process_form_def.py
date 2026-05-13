"""IStepFormDef for END_PROCESS."""

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

from __src__.views.components.canvas_checkbox import CanvasCheckbox

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class EndProcessFormDef(IStepFormDef):
    """Form definition for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.END_PROCESS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.END_PROCESS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Attendre avant de fermer:").pack(side=tk.LEFT, padx=(0, 5))
        dur_var = tk.StringVar(value="5")
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets["wait_duration"] = dur_var

        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            row0, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        widgets["wait_unit"] = unit_var

        # export data
        self._build_subform_clear_cache(frame, widgets)

        # ROW 1 — comment
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    def _build_subform_clear_cache(self, frame, widgets):
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        export_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row0, text="Exporter enregistrements textuels", variable=export_var).pack(
            side="left", padx=(0, 5)
        )
        widgets["export_data"] = export_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["wait_duration"].set(str(model.params.get("wait_duration", 5)))
        widgets["wait_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "wait_duration": safe_int_widget(widgets, "wait_duration", 0),
            "wait_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["wait_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if safe_int_widget(widgets, "wait_duration", -1) <= 0:
            errors.append("Durée d'attente : doit être >= 1")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        unit_time = model.params.get("wait_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        return f"Fin du processus\nAttendre {model.params.get('wait_duration', 0)} {unit_display} avant de quitter"


register_form(EndProcessFormDef())
