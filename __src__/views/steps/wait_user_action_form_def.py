"""IStepFormDef for WAIT_USER_ACTION."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, cast, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_user_action_params import WaitUserActionParams
from models.steps_context_model import StepsContext
from shared.constants import (
    C_MAXIMUM_WAIT_TIME,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    CONDITION_DISPLAY,
    CONDITION_MODEL_TO_VIEW,
    CONDITION_VIEW_TO_MODEL,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_POST_WAIT_DURATION: int = 3
C_INPUT_DEFAULT_CONDITION: str = CONDITION_DISPLAY[-1]  # "Toujours"

C_KEY_CONDITION = "condition"
C_KEY_WAIT_DURATION = "wait_duration"
C_KEY_WAIT_UNIT = "wait_unit"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WaitUserActionFormDef(IStepFormDef):
    """Form definition for the wait user action scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_USER_ACTION

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_USER_ACTION)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_condition(frame, widgets)
        self._build_subform_post_wait(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_condition(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the trigger condition combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_CONDITION tk.Variable.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Déclenche l'attente lorsque :").pack(side=tk.LEFT, padx=(0, 5))
        cond_var = tk.StringVar(value=C_INPUT_DEFAULT_CONDITION)
        ttk.Combobox(line1, textvariable=cond_var, values=CONDITION_DISPLAY, state="readonly").pack(
            side=tk.LEFT, padx=(0, 5),
        )
        widgets[C_KEY_CONDITION] = cond_var

    @staticmethod
    def _build_subform_post_wait(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the post-resume delay spinbox and time unit combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_WAIT_DURATION and C_KEY_WAIT_UNIT tk.Variables.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Délai post-reprise :").pack(side=tk.LEFT, padx=(0, 5))
        dur_var = tk.StringVar(value=str(C_INPUT_DEFAULT_POST_WAIT_DURATION))
        ttk.Spinbox(line2, from_=1, to=C_MAXIMUM_WAIT_TIME, textvariable=dur_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5),
        )
        unit_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(
            line2, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10,
        ).pack(side=tk.LEFT, padx=(0, 5))
        widgets[C_KEY_WAIT_DURATION] = dur_var
        widgets[C_KEY_WAIT_UNIT] = unit_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        p = cast(WaitUserActionParams, model.params)
        widgets[C_KEY_CONDITION].set(
            CONDITION_MODEL_TO_VIEW.get(p.condition, C_INPUT_DEFAULT_CONDITION),
        )
        widgets[C_KEY_WAIT_DURATION].set(str(p.wait_duration))
        widgets[C_KEY_WAIT_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(p.wait_unit, C_UNITS_TIME_DEFAULT_VIEW),
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
            C_KEY_CONDITION: CONDITION_VIEW_TO_MODEL.get(widgets[C_KEY_CONDITION].get()),
            C_KEY_WAIT_DURATION: safe_int_widget(widgets, C_KEY_WAIT_DURATION, -1),
            C_KEY_WAIT_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_WAIT_UNIT].get()),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int, steps_context: StepsContext) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        p = cast(WaitUserActionParams, model.params)
        cond_labels = {"success": "Si succès", "failure": "Si échec", "always": "Toujours"}
        condition = cond_labels.get(p.condition, "toujours")
        wd = p.wait_duration
        unit_time = p.wait_unit
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)

        delay_str = f"Si reprise demandée, patienter {wd} {unit_display}" if wd > 0 else ""
        return f"{condition} attendre action manuelle\n{delay_str}"


register_form(WaitUserActionFormDef())


# EOF
