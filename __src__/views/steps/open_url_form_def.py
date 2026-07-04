"""IStepFormDef implementation for the OPEN_URL step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_UNITS_TIME_ALLOWED_FOR_VIEW, C_UNITS_TIME_DEFAULT_VIEW
from shared.enums import StepTypeEnum, WaitUntilEnum
from shared.parse_util import safe_int_from_dict
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_DEFAULT_WAIT_UNTIL = WaitUntilEnum.E_IDLE.value
C_DEFAULT_TIMEOUT_DURATION = 12
C_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW

C_KEY_URL_CUT_AMPERSAND = "url_cut_ampersand"
C_KEY_URL_CUT_QUESTION = "url_cut_question"
C_KEY_URL_ALWAYS_ADD_SLASH = "url_always_add_slash"
C_KEY_WAIT_UNTIL = "wait_until"
C_KEY_WAIT_DNS_SOLVER = "wait_dns_solver"
C_KEY_TIMEOUT_DURATION = "timeout_duration"
C_KEY_TIMEOUT_UNIT = "timeout_unit"
C_KEY_COMMENT = "comment"
C_CHOICES_WAIT_PAGE_UNTIL = [WaitUntilEnum.E_DOM.value, WaitUntilEnum.E_LOAD.value, WaitUntilEnum.E_IDLE.value]

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class OpenUrlFormDef(IStepFormDef):
    """Builds the Open URL step form and handles its validation."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the workflow step handled by this form definition."""
        return StepTypeEnum.E_OPEN_URL

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        frame.columnconfigure(1, weight=1)

        self._build_subform_url_cutter(frame, widgets)
        self._build_subform_wait_until(frame, widgets)
        self._build_subform_timeout(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_url_cutter(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the URL cutter checkbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_URL_CUT_AMPERSAND tk.Variable.
        """
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))

        # ampersand
        url_cut_amp_var = tk.BooleanVar(value=True)
        CanvasCheckbox(row3, text="Couper '&...' de l'URL   ", variable=url_cut_amp_var).pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_URL_CUT_AMPERSAND] = url_cut_amp_var

        # question
        url_cut_question_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row3, text="Couper '?...' de l'URL   ", variable=url_cut_question_var).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_URL_CUT_QUESTION] = url_cut_question_var

        # always add slash
        url_always_add_slash_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row3, text="Terminer URL par un '/'", variable=url_always_add_slash_var).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_URL_ALWAYS_ADD_SLASH] = url_always_add_slash_var

    @staticmethod
    def _build_subform_wait_until(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the page load state combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_WAIT_UNTIL tk.Variable.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Attendre le chargement :").pack(side=tk.LEFT, padx=(0, 5))
        ws_var = tk.StringVar(value=C_DEFAULT_WAIT_UNTIL)
        ttk.Combobox(line2, textvariable=ws_var, values=C_CHOICES_WAIT_PAGE_UNTIL, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line2, text="(dom > load > idle 500ms)").pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_WAIT_UNTIL] = ws_var

    @staticmethod
    def _build_subform_timeout(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the timeout duration spinbox and time unit combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_TIMEOUT_DURATION and C_KEY_TIMEOUT_UNIT tk.Variables.
        """
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Timeout :").pack(side=tk.LEFT, padx=(0, 5))
        td_var = tk.StringVar(value=str(C_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tu_var = tk.StringVar(value=C_DEFAULT_TIMEOUT_UNIT)
        ttk.Combobox(line3, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        dns = tk.StringVar(value="6")
        ttk.Label(line3, text="Délai DNS (sec) :").pack(side=tk.LEFT, padx=(25, 5))
        ttk.Spinbox(line3, from_=1, to=30, textvariable=dns, width=4).pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_WAIT_DNS_SOLVER] = dns
        widgets[C_KEY_TIMEOUT_DURATION] = td_var
        widgets[C_KEY_TIMEOUT_UNIT] = tu_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        line4 = ttk.Frame(frame)
        line4.pack(fill="x", pady=(0, 8))

        ttk.Label(line4, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line4, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_URL_CUT_AMPERSAND].set(params_dict.get(C_KEY_URL_CUT_AMPERSAND, True))
        widgets[C_KEY_URL_CUT_QUESTION].set(params_dict.get(C_KEY_URL_CUT_QUESTION, False))
        widgets[C_KEY_URL_ALWAYS_ADD_SLASH].set(params_dict.get(C_KEY_URL_ALWAYS_ADD_SLASH, False))
        widgets[C_KEY_WAIT_UNTIL].set(params_dict.get(C_KEY_WAIT_UNTIL, C_DEFAULT_WAIT_UNTIL))
        widgets[C_KEY_WAIT_DNS_SOLVER].set(params_dict.get(C_KEY_WAIT_DNS_SOLVER, 6))
        widgets[C_KEY_TIMEOUT_DURATION].set(str(params_dict.get(C_KEY_TIMEOUT_DURATION, C_DEFAULT_TIMEOUT_DURATION)))
        widgets[C_KEY_TIMEOUT_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(params_dict.get(C_KEY_TIMEOUT_UNIT, ""), C_UNITS_TIME_DEFAULT_VIEW)
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
            C_KEY_URL_CUT_AMPERSAND: widgets[C_KEY_URL_CUT_AMPERSAND].get(),
            C_KEY_URL_CUT_QUESTION: widgets[C_KEY_URL_CUT_QUESTION].get(),
            C_KEY_URL_ALWAYS_ADD_SLASH: widgets[C_KEY_URL_ALWAYS_ADD_SLASH].get(),
            C_KEY_WAIT_UNTIL: widgets[C_KEY_WAIT_UNTIL].get(),
            C_KEY_WAIT_DNS_SOLVER: safe_int_from_dict(widgets, C_KEY_WAIT_DNS_SOLVER, -1),
            C_KEY_TIMEOUT_DURATION: safe_int_from_dict(widgets, C_KEY_TIMEOUT_DURATION, -1),
            C_KEY_TIMEOUT_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_TIMEOUT_UNIT].get()),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(OpenUrlFormDef())


# EOF
