"""IStepFormDef for JUMP_TO_STEP."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, cast, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps_context_model import StepsContext
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.components.column_combobox import ColumnCombobox
from views.steps._constants import CONDITION_DISPLAY, CONDITION_MODEL_TO_VIEW, CONDITION_VIEW_TO_MODEL

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_CONDITION = "condition"
C_KEY_STEPS_AVAILABLE = "_all_steps_available"
C_KEY_ALL_STEPS_ID_TO_INDEX = "_all_steps_id_to_index"
C_KEY_CHOICE_FROM_LISTBOX = "_choice_from_listbox"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class JumpToStepFormDef(IStepFormDef):
    """Form definition for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_JUMP_TO_STEP)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_condition(frame, widgets)
        self._build_subform_target_step(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_condition(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the jump trigger condition combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_CONDITION tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Condition:").pack(side=tk.LEFT, padx=(0, 5))
        cond_var = tk.StringVar(value=CONDITION_DISPLAY[0])
        ttk.Combobox(row0, textvariable=cond_var, values=CONDITION_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5),
        )
        widgets[C_KEY_CONDITION] = cond_var

    @staticmethod
    def _build_subform_target_step(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the target step combobox row, populated from C_KEY_STEPS_AVAILABLE.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_ALL_STEPS_ID_TO_INDEX and
                C_KEY_CHOICE_FROM_LISTBOX (ColumnCombobox widget).
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        available_steps: list[StepScrapingModel] = widgets.get(C_KEY_STEPS_AVAILABLE, [])

        all_steps_id_to_index = [s.step_id for s in available_steps]
        widgets[C_KEY_ALL_STEPS_ID_TO_INDEX] = all_steps_id_to_index

        ttk.Label(row1, text="Sauter vers :").pack(side=tk.LEFT, padx=(0, 5))

        ccb = ColumnCombobox(row1, state="readonly")
        ccb.add_column("step_id_hidden", lambda s: s.step_id, width=0, visible=False)
        ccb.add_column("index", lambda _: "", width=40, visible=True)
        ccb.add_column("step_id", lambda s: s.step_id, width=60, visible=True)
        ccb.add_column("step_type", lambda s: C_STEP_TYPE_TO_LABELS.get(s.step_type), width=120, visible=True)
        for i, s in enumerate(available_steps):
            ccb.add_item(s, columns=[s.step_id, str(i + 1).zfill(2), s.step_id, C_STEP_TYPE_TO_LABELS.get(s.step_type)])
        if available_steps:
            ccb.current(0)
        ccb.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_CHOICE_FROM_LISTBOX] = ccb

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
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        p = cast(JumpToStepParams, model.params)
        widgets[C_KEY_CONDITION].set(CONDITION_MODEL_TO_VIEW.get(p.condition, CONDITION_DISPLAY[0]))

        target_hexastring = p.target_hexastring
        ccb: ColumnCombobox = widgets[C_KEY_CHOICE_FROM_LISTBOX]
        all_steps_id_to_index: list[str] = widgets.get(C_KEY_ALL_STEPS_ID_TO_INDEX, [])
        if target_hexastring and target_hexastring in all_steps_id_to_index:
            ccb.current(all_steps_id_to_index.index(target_hexastring))
        elif ccb.size() > 0:
            ccb.current(0)

        widgets[C_KEY_COMMENT].set(p.comment)

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        cond_display = widgets[C_KEY_CONDITION].get()
        ccb: ColumnCombobox = widgets.get(C_KEY_CHOICE_FROM_LISTBOX)
        selected_step: StepScrapingModel | None = ccb.get_selected_object() if ccb else None
        hexastring = selected_step.step_id if selected_step is not None else ""
        return {
            C_KEY_CONDITION: CONDITION_VIEW_TO_MODEL.get(cond_display),
            "target_hexastring": hexastring,
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
        p = cast(JumpToStepParams, model.params)
        target_hexastring = p.target_hexastring or "????"

        idx_found = steps_context.find_index_by_id(target_hexastring)
        if idx_found is None:
            target_hexastring = "????"
            target_index = "??"
        else:
            target_index = str(idx_found + 1).zfill(2)

        cond = p.condition
        if cond == "success":
            return f"Si le résultat est un succès\nSe rendre à l'étape {target_index}.  #{target_hexastring}"
        if cond == "failure":
            return f"Si le résultat est un échec\nSe rendre à l'étape {target_index}.  #{target_hexastring}"
        return f"Si le résultat est un succès/échec\nToujours aller à l'étape {target_index}.  #{target_hexastring}"


register_form(JumpToStepFormDef())


# EOF
