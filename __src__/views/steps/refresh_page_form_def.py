"""IStepFormDef for REFRESH_PAGE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, cast, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from models.steps.refresh_page_params import RefreshPageParams
from models.steps_context_model import StepsContext
from shared.constants import (
    C_MAXIMUM_WAIT_TIME,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import (
    C_CHOICES_WAIT_PAGE_STATE,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_WAIT_STATE = C_CHOICES_WAIT_PAGE_STATE[-1]
C_INPUT_DEFAULT_TIMEOUT_DURATION = 10
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW

C_KEY_CLEAR_CACHE = "clear_cache"
C_KEY_WAIT_STATE = "wait_state"
C_KEY_TIMEOUT_DURATION = "timeout_duration"
C_KEY_TIMEOUT_UNIT = "timeout_unit"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class RefreshPageFormDef(IStepFormDef):
    """Form definition for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_REFRESH_PAGE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_REFRESH_PAGE)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_clear_cache(frame, widgets)
        self._build_subform_wait_state(frame, widgets)
        self._build_subform_timeout(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_clear_cache(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the clear-cache checkbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_CLEAR_CACHE tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        cache_var = tk.BooleanVar(value=False)
        CanvasCheckbox(row0, text="Vider le cache (Ctrl + F5)", variable=cache_var).pack(side="left", padx=(0, 5))
        widgets[C_KEY_CLEAR_CACHE] = cache_var

    @staticmethod
    def _build_subform_wait_state(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the page load state combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_WAIT_STATE tk.Variable.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Attendre le chargement :").pack(side=tk.LEFT, padx=(0, 5))
        ws_var = tk.StringVar(value=C_INPUT_DEFAULT_WAIT_STATE)
        ttk.Combobox(line1, textvariable=ws_var, values=C_CHOICES_WAIT_PAGE_STATE, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5),
        )
        ttk.Label(line1, text="(dom > load > idle 500ms)").pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_WAIT_STATE] = ws_var

    @staticmethod
    def _build_subform_timeout(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the timeout duration spinbox and time unit combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_TIMEOUT_DURATION and C_KEY_TIMEOUT_UNIT tk.Variables.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Timeout :").pack(side=tk.LEFT, padx=(0, 5))
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_WAIT_TIME, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5),
        )
        tu_var = tk.StringVar(value=C_INPUT_DEFAULT_TIMEOUT_UNIT)
        ttk.Combobox(line2, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10).pack(
            side=tk.LEFT, padx=(0, 5),
        )
        widgets[C_KEY_TIMEOUT_DURATION] = td_var
        widgets[C_KEY_TIMEOUT_UNIT] = tu_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Commentaire :").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        p = cast(RefreshPageParams, model.params)
        widgets[C_KEY_CLEAR_CACHE].set(p.clear_cache)
        widgets[C_KEY_WAIT_STATE].set(p.wait_state)
        widgets[C_KEY_TIMEOUT_DURATION].set(str(p.timeout_duration))
        widgets[C_KEY_TIMEOUT_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(p.timeout_unit, C_UNITS_TIME_DEFAULT_VIEW),
        )
        widgets[C_KEY_COMMENT].set(p.comment)

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        return {
            C_KEY_CLEAR_CACHE: bool(widgets[C_KEY_CLEAR_CACHE].get()),
            C_KEY_WAIT_STATE: widgets[C_KEY_WAIT_STATE].get(),
            C_KEY_TIMEOUT_DURATION: safe_int_widget(widgets, C_KEY_TIMEOUT_DURATION, -1),
            C_KEY_TIMEOUT_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_TIMEOUT_UNIT].get()),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int, steps_context: StepsContext) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.
            steps_context: Step execution context.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        p = cast(RefreshPageParams, model.params)
        mode_clear_cache = "Vide le cache (Ctrl+F5)" if p.clear_cache else "Garde le cache (F5)"
        timeout = p.timeout_duration
        unit_time = p.timeout_unit
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)

        return (
            f"Rafraîchir la page  -  timeout : {timeout} {unit_display}\n"
             f"{mode_clear_cache}  -  Attendre : {p.wait_state}"
        )


register_form(RefreshPageFormDef())


# EOF
