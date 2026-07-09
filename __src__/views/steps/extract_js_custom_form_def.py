"""IStepFormDef for EXTRACT_JS_CUSTOM."""

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

C_KEY_SELECTOR = "js_code"
C_KEY_QUALITY_EXPECTED = "quality_expected"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ExtractJsCustomFormDef(IStepFormDef):
    """Form definition for the custom JS extraction step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXTRACT_JS_CUSTOM

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with widget/variable references keyed by C_KEY_* constants.
        """
        self._build_subform_js_code(frame, widgets)
        self._build_subform_qual_key(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_js_code(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the JS code input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_SELECTOR tk.Text widget.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Code JS :").pack(side=tk.LEFT, padx=(0, 5), anchor="n")
        js_text = tk.Text(row0, height=3, wrap="none", font=("Courier New", 9))
        js_text.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_SELECTOR] = js_text

    @staticmethod
    def _build_subform_qual_key(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the quality expected input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_QUALITY_EXPECTED tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Qualité attendue (qté de champs alimentés) :").pack(side=tk.LEFT, padx=(0, 5))
        qual_key_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=qual_key_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_QUALITY_EXPECTED] = qual_key_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))

        ttk.Label(row3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable/tk.Text reference.
        """
        js_text: tk.Text = widgets[C_KEY_SELECTOR]
        js_text.delete("1.0", "end")
        js_text.insert("1.0", params_dict.get(C_KEY_SELECTOR, ""))

        widgets[C_KEY_QUALITY_EXPECTED].set(params_dict.get(C_KEY_QUALITY_EXPECTED, ""))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable/tk.Text reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        js_text: tk.Text = widgets[C_KEY_SELECTOR]
        return {
            C_KEY_SELECTOR: js_text.get("1.0", "end-1c").strip(),
            C_KEY_QUALITY_EXPECTED: widgets[C_KEY_QUALITY_EXPECTED].get().strip(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(ExtractJsCustomFormDef())


# EOF
