"""IStepFormDef implementation for the RESTART_TO_BEGINNING step."""

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

C_JUMP_ONLY_IF_URLS_REMAINING = "jump_only_if_urls_remaining"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class RestartToBeginningFormDef(IStepFormDef):
    """Builds the Restart to Beginning step form and handles its validation."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the workflow step handled by this form definition."""
        return StepTypeEnum.E_RESTART_TO_BEGINNING

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        urls_var = tk.BooleanVar(value=True)

        CanvasCheckbox(line1, text="Recommencer uniquement s'il reste des URLs (sinon SKIP)", variable=urls_var).pack(
            side=tk.LEFT, padx=(0, 25)
        )
        widgets[C_JUMP_ONLY_IF_URLS_REMAINING] = urls_var

        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot."""
        widgets[C_JUMP_ONLY_IF_URLS_REMAINING].set(bool(params_dict.get(C_JUMP_ONLY_IF_URLS_REMAINING, True)))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict."""
        return {
            C_JUMP_ONLY_IF_URLS_REMAINING: widgets[C_JUMP_ONLY_IF_URLS_REMAINING].get(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(RestartToBeginningFormDef())


# EOF
