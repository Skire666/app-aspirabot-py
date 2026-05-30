"""IStepFormDef for JUMP_TO_STEP."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from shared.step_view_item import StepViewItem
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
C_KEY_TARGET_HEXASTRING = "target_hexastring"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class JumpToStepFormDef(IStepFormDef):
    """Form definition for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP

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
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
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

        available_items: list[StepViewItem] = widgets.get(C_KEY_STEPS_AVAILABLE, [])

        all_steps_id_to_index = [item.step_id for item in available_items]
        widgets[C_KEY_ALL_STEPS_ID_TO_INDEX] = all_steps_id_to_index

        ttk.Label(row1, text="Sauter vers :").pack(side=tk.LEFT, padx=(0, 5))

        ccb = ColumnCombobox(row1, state="readonly")
        ccb.add_column("step_id_hidden", lambda item: item.step_id, width=0, visible=False)
        ccb.add_column("index", lambda _: "", width=40, visible=True)
        ccb.add_column("step_id", lambda item: item.step_id, width=60, visible=True)
        ccb.add_column("step_type", lambda item: C_STEP_TYPE_TO_LABELS.get(item.step_type), width=120, visible=True)
        for i, item in enumerate(available_items):
            idx_disp = str(i + 1).zfill(2)
            ccb.add_item(
                item, columns=[item.step_id, idx_disp, item.step_id, C_STEP_TYPE_TO_LABELS.get(item.step_type)]
            )
        if available_items:
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
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        condition = params_dict.get(C_KEY_CONDITION, "")
        widgets[C_KEY_CONDITION].set(CONDITION_MODEL_TO_VIEW.get(condition, CONDITION_DISPLAY[0]))

        target_hexastring = params_dict.get(C_KEY_TARGET_HEXASTRING, "")
        ccb: ColumnCombobox = widgets[C_KEY_CHOICE_FROM_LISTBOX]
        all_steps_id_to_index: list[str] = widgets.get(C_KEY_ALL_STEPS_ID_TO_INDEX, [])
        if target_hexastring and target_hexastring in all_steps_id_to_index:
            ccb.current(all_steps_id_to_index.index(target_hexastring))
        elif ccb.size() > 0:
            ccb.current(0)

        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

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
        selected_item: StepViewItem | None = ccb.get_selected_object() if ccb else None
        hexastring = selected_item.step_id if selected_item is not None else ""
        return {
            C_KEY_CONDITION: CONDITION_VIEW_TO_MODEL.get(cond_display),
            C_KEY_TARGET_HEXASTRING: hexastring,
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(JumpToStepFormDef())


# EOF
