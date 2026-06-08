"""IStepFormDef for EXTRACT_VARIABLE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from shared.enums import StepTypeEnum
from shared.step_registry import register_form
from views.steps._constants import EXPORT_VAR_DISPLAY, EXPORT_VAR_MODEL_TO_VIEW, EXPORT_VAR_VIEW_TO_MODEL

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_VARIABLE = "variable"
C_KEY_MAPPING = "mapping"
C_KEY_COMMENT = "comment"

C_EXPORT_VAR_VALUES: list[str] = ["datetime_now", "last_url_full", "last_url_domain", "last_url_cutted"]

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ExtractVariableFormDef(IStepFormDef):
    """Form definition for the export variable step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXTRACT_VARIABLE

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by C_KEY_* constants.
        """
        self._build_subform_variable(frame, widgets)
        self._build_subform_mapping(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_variable(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the variable selection combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_VARIABLE tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Variable :").pack(side=tk.LEFT, padx=(0, 5))
        var_var = tk.StringVar(value=EXPORT_VAR_DISPLAY[0])
        ttk.Combobox(row0, textvariable=var_var, values=EXPORT_VAR_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets[C_KEY_VARIABLE] = var_var

    @staticmethod
    def _build_subform_mapping(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the mapping key input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_MAPPING tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Clé/Mapping :").pack(side=tk.LEFT, padx=(0, 5))
        mapping_var = tk.StringVar(value="last_url | datetime_now")
        ttk.Entry(row1, textvariable=mapping_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_MAPPING] = mapping_var

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
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_VARIABLE].set(
            EXPORT_VAR_MODEL_TO_VIEW.get(params_dict.get(C_KEY_VARIABLE, ""), EXPORT_VAR_DISPLAY[0])
        )
        widgets[C_KEY_MAPPING].set(params_dict.get(C_KEY_MAPPING, ""))
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
            C_KEY_VARIABLE: EXPORT_VAR_VIEW_TO_MODEL.get(widgets[C_KEY_VARIABLE].get(), C_EXPORT_VAR_VALUES[-1]),
            C_KEY_MAPPING: widgets[C_KEY_MAPPING].get().strip(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(ExtractVariableFormDef())


# EOF
