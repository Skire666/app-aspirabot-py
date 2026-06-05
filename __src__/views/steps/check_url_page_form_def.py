"""IStepFormDef implementation for the CHECK_URL_PAGE step."""

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

from __src__.views.components.canvas_checkbox import CanvasCheckbox

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_CHECK_DOMAIN = "check_domain"
C_CHECK_PATH = "check_path"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CheckUrlPageFormDef(IStepFormDef):
    """Builds the Check URL Page step form and handles its validation."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the workflow step handled by this form definition."""
        return StepTypeEnum.E_CHECK_URL_PAGE

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame."""
        frame.columnconfigure(1, weight=1)

        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        domain_var = tk.BooleanVar(value=True)
        path_var = tk.BooleanVar(value=False)

        CanvasCheckbox(line1, text="Vérifier le domaine ( [xxx.com]/yyy/ )", variable=domain_var).pack(
            side=tk.LEFT, padx=(0, 25)
        )
        CanvasCheckbox(line1, text="Vérifier le chemin ( xxx.com[/yyy]/ )", variable=path_var).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_CHECK_DOMAIN] = domain_var
        widgets[C_CHECK_PATH] = path_var

        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot."""
        widgets[C_CHECK_DOMAIN].set(bool(params_dict.get(C_CHECK_DOMAIN, True)))
        widgets[C_CHECK_PATH].set(bool(params_dict.get(C_CHECK_PATH)))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict."""
        return {
            C_CHECK_DOMAIN: widgets[C_CHECK_DOMAIN].get(),
            C_CHECK_PATH: widgets[C_CHECK_PATH].get(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(CheckUrlPageFormDef())


# EOF
