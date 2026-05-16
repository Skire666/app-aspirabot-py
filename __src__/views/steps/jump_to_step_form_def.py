"""IStepFormDef for JUMP_TO_STEP."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import CONDITION_DISPLAY, CONDITION_MODEL_TO_VIEW, CONDITION_VIEW_TO_MODEL

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_KEY_CONDITION = "condition"
C_KEY_STEPS_AVAILABLE = "_all_steps_available"
C_KEY_ALL_CHOICES_LISTBOX = "_all_choices_listbox"
C_KEY_ALL_STEPS_ID_TO_INDEX = "_all_steps_id_to_index"
C_KEY_ALL_HEXASTRING_TO_MODEL = "_all_hexastring_to_model"
C_KEY_CHOICE_FROM_LISTBOX = "_choice_from_listbox"
C_KEY_COMMENT = "comment"

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


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
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets[C_KEY_CONDITION] = cond_var

    def _build_subform_target_step(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the target step combobox row, populated from C_KEY_STEPS_AVAILABLE.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_ALL_CHOICES_LISTBOX,
                C_KEY_ALL_STEPS_ID_TO_INDEX, C_KEY_ALL_HEXASTRING_TO_MODEL, and
                C_KEY_CHOICE_FROM_LISTBOX tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        available_steps: list[StepScrapingModel] = widgets.get(C_KEY_STEPS_AVAILABLE, [])

        # Build display strings and lookup structures for available steps
        all_choices_listbox = []
        all_steps_id_to_index = []
        all_hexastring_to_model = {}
        for index, s in enumerate(available_steps):
            choice_str = self.compute_string_displayed_in_combobox(index, s)
            all_choices_listbox.append(choice_str)
            all_steps_id_to_index.append(s.step_id)
            all_hexastring_to_model[s.step_id] = s
        widgets[C_KEY_ALL_CHOICES_LISTBOX] = all_choices_listbox
        widgets[C_KEY_ALL_STEPS_ID_TO_INDEX] = all_steps_id_to_index
        widgets[C_KEY_ALL_HEXASTRING_TO_MODEL] = all_hexastring_to_model

        default_choice = all_choices_listbox[0] if all_choices_listbox else ""
        target_var = tk.StringVar(value=default_choice)
        widgets[C_KEY_CHOICE_FROM_LISTBOX] = target_var

        ttk.Label(row1, text="Sauter vers :").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(row1, textvariable=target_var, values=all_choices_listbox, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )

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
        cond_model = model.params.get(C_KEY_CONDITION, "success")
        widgets[C_KEY_CONDITION].set(CONDITION_MODEL_TO_VIEW.get(cond_model, CONDITION_DISPLAY[0]))

        all_hexastring_to_model = widgets.get(C_KEY_ALL_HEXASTRING_TO_MODEL, [])
        all_choices_listbox = widgets.get(C_KEY_ALL_CHOICES_LISTBOX, [])
        target_hexastring = model.params.get("target_hexastring", "")

        choice_str = all_choices_listbox[0] if all_choices_listbox else ""

        if target_hexastring is not None and all_choices_listbox:
            all_steps_id_to_index = widgets.get(C_KEY_ALL_STEPS_ID_TO_INDEX, [])
            index_target = (
                all_steps_id_to_index.index(target_hexastring)
                if target_hexastring in all_steps_id_to_index
                else -1
            )
            model_target = all_hexastring_to_model.get(target_hexastring)
            choice_str = self.compute_string_displayed_in_combobox(index_target, model_target)

        widgets[C_KEY_CHOICE_FROM_LISTBOX].set(choice_str)
        widgets[C_KEY_COMMENT].set(model.params.get(C_KEY_COMMENT, ""))

    @staticmethod
    def compute_string_displayed_in_combobox(index: int, model: StepScrapingModel) -> str:
        """Format the display string for a step entry in the jump-target combobox.

        Args:
            index: Zero-based position of the step in the workflow.
            model: The target step model.

        Returns:
            A formatted string like "01.  -  #hxst  - <label>", or an empty string
            if the index is negative or the model is None.
        """
        if index >= 0 and model is not None:
            return (
                f"{str(index + 1).zfill(2)}.  -  #{model.step_id}  - {C_STEP_TYPE_TO_LABELS.get(model.step_type)}"
            )
        return ""

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        cond_display = widgets[C_KEY_CONDITION].get()
        choice_target_hexastring = widgets.get(C_KEY_CHOICE_FROM_LISTBOX, "").get()
        hexastring = self._extract_after_hash_hexastring(choice_target_hexastring)
        return {
            C_KEY_CONDITION: CONDITION_VIEW_TO_MODEL.get(cond_display),
            "target_hexastring": hexastring,
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @staticmethod
    def _extract_after_hash_hexastring(choice_target_hexastring: str) -> str:
        """Extract the 4-character hex step ID from a combobox display string.

        Args:
            choice_target_hexastring: A string of the form "01.  -  #hxst  - <label>".

        Returns:
            The 4-character hex string following '#', or an empty string if not found.
        """
        if choice_target_hexastring is not None:
            hash_index = choice_target_hexastring.find("#")
            if hash_index != -1:
                return choice_target_hexastring[hash_index + 1 : hash_index + 5]
        return ""

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        target_hexastring = model.params.get("target_hexastring", "????")

        target_index = ""
        for index_target, step_item in enumerate(model.parent_context):
            if step_item.step_id == target_hexastring:
                target_index = f"{index_target + 1}".zfill(2)
                break

        if not target_index:
            target_hexastring = "????"
            target_index = "??"

        cond = model.params.get(C_KEY_CONDITION, "success")
        if cond == "success":
            return f"Si le résultat est un succès\nSe rendre à l'étape {target_index}.  #{target_hexastring}"
        if cond == "failure":
            return f"Si le résultat est un échec\nSe rendre à l'étape {target_index}.  #{target_hexastring}"
        return (
            f"Si le résultat est un succès/échec\nToujours aller à l'étape {target_index}.  #{target_hexastring}"
        )


register_form(JumpToStepFormDef())
