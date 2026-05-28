"""IStepFormDef for END_PROCESS."""

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
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_WAIT_DURATION = "wait_duration"
C_KEY_WAIT_UNIT = "wait_unit"
C_KEY_EXPORT_DATA = "export_data"
C_KEY_COMMENT = "comment"

C_DEFAULT_WAIT_DURATION = 3

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class KillBrowserFormDef(IStepFormDef):
    """Form definition for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_KILL_BROWSER

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_KILL_BROWSER)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_wait_duration(frame, widgets)
        self._build_subform_export_data(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_wait_duration(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the pre-close delay spinbox and time unit combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_WAIT_DURATION and C_KEY_WAIT_UNIT tk.Variables.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Attendre avant de fermer:").pack(side=tk.LEFT, padx=(0, 5))
        dur_var = tk.StringVar(value=str(C_DEFAULT_WAIT_DURATION))
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5),
        )
        widgets[C_KEY_WAIT_DURATION] = dur_var

        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            row0, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12,
        ).pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_WAIT_UNIT] = unit_var

    @staticmethod
    def _build_subform_export_data(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the export records checkbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_EXPORT_DATA tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        export_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row1, text="Exporter enregistrements textuels", variable=export_var).pack(
            side="left", padx=(0, 5),
        )
        widgets[C_KEY_EXPORT_DATA] = export_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_WAIT_DURATION].set(str(model.params.get(C_KEY_WAIT_DURATION, C_DEFAULT_WAIT_DURATION)))
        widgets[C_KEY_WAIT_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get(C_KEY_WAIT_UNIT, C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW,
            ),
        )
        widgets[C_KEY_COMMENT].set(model.params.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        return {
            C_KEY_WAIT_DURATION: safe_int_widget(widgets, C_KEY_WAIT_DURATION, -1),
            C_KEY_WAIT_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_WAIT_UNIT].get()),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        unit_time = model.params.get(C_KEY_WAIT_UNIT, "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        qty_time = model.params.get(C_KEY_WAIT_DURATION, 0)
        return f"Quitter navigateur\nAttendre {qty_time} {unit_display} avant de quitter"


register_form(KillBrowserFormDef())
