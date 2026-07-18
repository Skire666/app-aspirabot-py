"""IStepFormDef for EXPORT_DATA_TO_CSV."""

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

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_EXPORT = "export"  # export_urls_done_2026-06-07_09h21m29s028210.json

C_KEY_PREFIX = "csv_filename"
C_KEY_AGGREGATORS = "aggregators_list"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ExportDataToJsFormDef(IStepFormDef):
    """Form definition for the export data to JavaScript scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXPORT_DATA_TO_CSV

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_prefix(frame, widgets)
        self._build_subform_aggregator(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_prefix(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the file prefix input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_PREFIX tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Préfixe fichier :").pack(side=tk.LEFT, padx=(0, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_EXPORT)
        ttk.Entry(row0, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_PREFIX] = sel_var

    @staticmethod
    def _build_subform_aggregator(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the JS code input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_SELECTOR tk.Text widget.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Agréger\na = e0.b\ne6.a=e1.b").pack(side=tk.LEFT, padx=(0, 5), anchor="n")
        js_text = tk.Text(row0, height=3, wrap="none", font=("Courier New", 9))
        js_text.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_AGGREGATORS] = js_text

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
        js_text: tk.Text = widgets[C_KEY_AGGREGATORS]
        js_text.delete("1.0", "end")
        js_text.insert("1.0", params_dict.get(C_KEY_AGGREGATORS, ""))

        widgets[C_KEY_PREFIX].set(params_dict.get(C_KEY_PREFIX, C_INPUT_DEFAULT_EXPORT))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        js_text: tk.Text = widgets[C_KEY_AGGREGATORS]

        return {
            C_KEY_PREFIX: widgets[C_KEY_PREFIX].get().strip(),
            C_KEY_AGGREGATORS: js_text.get("1.0", "end-1c").strip(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(ExportDataToJsFormDef())

# EOF
