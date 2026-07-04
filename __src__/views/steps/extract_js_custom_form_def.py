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
from views.components.canvas_checkbox import CanvasCheckbox

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_SELECTOR = "js_code"
C_KEY_MAIN_MAPPING = "primary_key"
C_KEY_URL_CUT_AMPERSAND = "url_cut_ampersand"
C_KEY_URL_CUT_QUESTION = "url_cut_question"
C_KEY_URL_ALWAYS_ADD_SLASH = "url_always_add_slash"
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
        self._build_subform_primary_key(frame, widgets)
        self._build_subform_url_cutter(frame, widgets)
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
        js_text = tk.Text(row0, height=1, wrap="none", font=("Courier New", 9))
        js_text.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_SELECTOR] = js_text

    @staticmethod
    def _build_subform_primary_key(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the primary key input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_MAIN_MAPPING tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Clé primaire :").pack(side=tk.LEFT, padx=(0, 5))
        primary_key_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=primary_key_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_MAIN_MAPPING] = primary_key_var

    @staticmethod
    def _build_subform_url_cutter(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the URL cutter checkbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_URL_CUT_AMPERSAND tk.Variable.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        # ampersand
        url_cut_amp_var = tk.BooleanVar(value=True)
        CanvasCheckbox(row2, text="Couper '&...' de l'URL   ", variable=url_cut_amp_var).pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_URL_CUT_AMPERSAND] = url_cut_amp_var

        # question
        url_cut_question_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row2, text="Couper '?...' de l'URL   ", variable=url_cut_question_var).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_URL_CUT_QUESTION] = url_cut_question_var

        # always add slash
        url_always_add_slash_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row2, text="Terminer URL par un '/'", variable=url_always_add_slash_var).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_URL_ALWAYS_ADD_SLASH] = url_always_add_slash_var

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

        widgets[C_KEY_MAIN_MAPPING].set(params_dict.get(C_KEY_MAIN_MAPPING, ""))
        widgets[C_KEY_URL_CUT_AMPERSAND].set(params_dict.get(C_KEY_URL_CUT_AMPERSAND, True))
        widgets[C_KEY_URL_CUT_QUESTION].set(params_dict.get(C_KEY_URL_CUT_QUESTION, False))
        widgets[C_KEY_URL_ALWAYS_ADD_SLASH].set(params_dict.get(C_KEY_URL_ALWAYS_ADD_SLASH, False))
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
            C_KEY_MAIN_MAPPING: widgets[C_KEY_MAIN_MAPPING].get().strip(),
            C_KEY_URL_CUT_AMPERSAND: widgets[C_KEY_URL_CUT_AMPERSAND].get(),
            C_KEY_URL_CUT_QUESTION: widgets[C_KEY_URL_CUT_QUESTION].get(),
            C_KEY_URL_ALWAYS_ADD_SLASH: widgets[C_KEY_URL_ALWAYS_ADD_SLASH].get(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(ExtractJsCustomFormDef())


# EOF
