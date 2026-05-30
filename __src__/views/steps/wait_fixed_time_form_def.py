"""IStepFormDef for WAIT_FIXED_TIME."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from shared.constants import C_MAXIMUM_WAIT_TIME, C_UNITS_TIME_ALLOWED_FOR_VIEW, C_UNITS_TIME_DEFAULT_VIEW
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_from_dict

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_DURATION = 3

C_KEY_DURATION = "duration"
C_KEY_UNIT_TIME = "unit"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WaitFixedTimeFormDef(IStepFormDef):
    """Form definition for the wait fixed time scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_FIXED_TIME

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_FIXED_TIME)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_duration(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_duration(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the duration spinbox and time unit combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_DURATION and C_KEY_UNIT_TIME tk.Variables.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Attendre une durée de :").pack(side=tk.LEFT, padx=(0, 5))
        dur_var = tk.StringVar(value=str(C_INPUT_DEFAULT_DURATION))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_DURATION] = dur_var

        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            line1, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_UNIT_TIME] = unit_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_DURATION].set(str(params_dict.get(C_KEY_DURATION, C_INPUT_DEFAULT_DURATION)))
        widgets[C_KEY_UNIT_TIME].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(params_dict.get(C_KEY_UNIT_TIME, ""), C_UNITS_TIME_DEFAULT_VIEW)
        )
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        return {
            C_KEY_DURATION: safe_int_from_dict(widgets, C_KEY_DURATION, -1),
            C_KEY_UNIT_TIME: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_UNIT_TIME].get()),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(WaitFixedTimeFormDef())


# EOF
