"""IStepFormDef implementation for the OPEN_URL step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import (
    C_KEY_URL_MODE,
    C_MAXIMUM_SIZE_IMAGE,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import OpenUrlModeEnum, StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    C_CHOICES_WAIT_PAGE_STATE,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_URL_MODE = OpenUrlModeEnum.E_SOURCE.value
C_INPUT_DEFAULT_URL = "https://example.com/"
C_INPUT_DEFAULT_WAIT_STATE = C_CHOICES_WAIT_PAGE_STATE[-1]
C_INPUT_DEFAULT_TIMEOUT_DURATION = 10
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW

C_KEY_URL_CUSTOM = "url_custom"
C_KEY_WAIT_STATE = "wait_state"
C_KEY_WAIT_DNS_SOLVER = "wait_dns_solver"
C_KEY_TIMEOUT_DURATION = "timeout_duration"
C_KEY_TIMEOUT_UNIT = "timeout_unit"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class OpenUrlFormDef(IStepFormDef):
    """Builds the Open URL step form and handles its validation."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the workflow step handled by this form definition."""
        return StepTypeEnum.E_OPEN_URL

    @classmethod
    def label(cls) -> str:
        """Return the label shown in the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_OPEN_URL)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        frame.columnconfigure(1, weight=1)

        self._build_subform_url(frame, widgets)
        self._build_subform_wait_state(frame, widgets)
        self._build_subform_timeout(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_url(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the URL mode radio buttons and custom URL entry row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_URL_MODE and C_KEY_URL_CUSTOM tk.Variables.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        url_mode_var = tk.StringVar(value=C_INPUT_DEFAULT_URL_MODE)
        url_custom_var = tk.StringVar(value=C_INPUT_DEFAULT_URL)

        # Mode selection radio buttons
        OpenUrlFormDef._build_url_mode_buttons(line1, url_mode_var)

        url_entry = ttk.Entry(line1, textvariable=url_custom_var)
        url_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_URL_MODE] = url_mode_var
        widgets[C_KEY_URL_CUSTOM] = url_custom_var

        # Keep the entry state in sync with the selected mode
        OpenUrlFormDef._bind_url_mode_entry(url_mode_var, url_entry)

    @staticmethod
    def _build_url_mode_buttons(line1: ttk.Frame, url_mode_var: tk.StringVar) -> None:
        """Build the URL source radio buttons.

        Args:
            line1: Frame to pack the radio buttons into.
            url_mode_var: StringVar that receives the selected mode value.
        """
        tk.Radiobutton(
            line1,
            text="Lire la prochaine URL",
            variable=url_mode_var,
            value=OpenUrlModeEnum.E_SOURCE.value,
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            line1,
            text="URL personnalisée",
            variable=url_mode_var,
            value=OpenUrlModeEnum.E_CUSTOM.value,
        ).pack(side=tk.LEFT, padx=(0, 5))

    @staticmethod
    def _bind_url_mode_entry(url_mode_var: tk.StringVar, url_entry: ttk.Entry) -> None:
        """Synchronize the URL entry enabled state with the selected mode.

        Args:
            url_mode_var: StringVar holding the current URL mode.
            url_entry: Entry widget to enable or disable based on the mode.
        """

        def _sync_url_entry_state(*_args: object) -> None:
            state = "readonly" if url_mode_var.get() == OpenUrlModeEnum.E_SOURCE.value else "normal"
            url_entry.configure(state=state)

        # React to mode changes and initialize the current state
        url_mode_var.trace_add("write", _sync_url_entry_state)
        _sync_url_entry_state()

    @staticmethod
    def _build_subform_wait_state(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the page load state combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_WAIT_STATE tk.Variable.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Attendre le chargement :").pack(side=tk.LEFT, padx=(0, 5))
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(line2, textvariable=ws_var, values=C_CHOICES_WAIT_PAGE_STATE, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line2, text="(dom > load > idle 500ms)").pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_WAIT_STATE] = ws_var

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
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)
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
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_URL_MODE].set(model.params.get(C_KEY_URL_MODE, C_INPUT_DEFAULT_URL_MODE))
        widgets[C_KEY_URL_CUSTOM].set(model.params.get(C_KEY_URL_CUSTOM, C_INPUT_DEFAULT_URL))
        widgets[C_KEY_WAIT_STATE].set(model.params.get(C_KEY_WAIT_STATE, C_INPUT_DEFAULT_WAIT_STATE))
        widgets[C_KEY_WAIT_DNS_SOLVER].set(model.params.get(C_KEY_WAIT_DNS_SOLVER, 6))
        widgets[C_KEY_TIMEOUT_DURATION].set(
            str(model.params.get(C_KEY_TIMEOUT_DURATION, C_INPUT_DEFAULT_TIMEOUT_DURATION))
        )
        widgets[C_KEY_TIMEOUT_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get(C_KEY_TIMEOUT_UNIT, C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
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
            C_KEY_URL_MODE: widgets[C_KEY_URL_MODE].get(),
            C_KEY_URL_CUSTOM: widgets[C_KEY_URL_CUSTOM].get().strip(),
            C_KEY_WAIT_STATE: widgets[C_KEY_WAIT_STATE].get(),
            C_KEY_WAIT_DNS_SOLVER: safe_int_widget(widgets, C_KEY_WAIT_DNS_SOLVER, -1),
            C_KEY_TIMEOUT_DURATION: safe_int_widget(widgets, C_KEY_TIMEOUT_DURATION, -1),
            C_KEY_TIMEOUT_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_TIMEOUT_UNIT].get()),
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
        timeout = model.params.get(C_KEY_TIMEOUT_DURATION, 0)
        unit_time = model.params.get(C_KEY_TIMEOUT_UNIT, "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        url_mode = model.params.get(C_KEY_URL_MODE)

        url_used = (
            "Prochaine URL dans la source"
            if url_mode == OpenUrlModeEnum.E_SOURCE.value
            else f"Url : {model.params.get(C_KEY_URL_CUSTOM, '')}"
        )

        return f"Ouvrir une URL  -  timeout : {timeout} {unit_display}\n{url_used}"


register_form(OpenUrlFormDef())
