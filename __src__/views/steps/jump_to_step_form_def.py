"""IStepFormDef for JUMP_TO_STEP."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import CONDITION_DISPLAY, CONDITION_MODEL_TO_VIEW, CONDITION_VIEW_TO_MODEL

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class JumpToStepFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.JUMP_TO_STEP

    @classmethod
    def label(cls) -> str:
        return "Si le résultat est un ..."

    @staticmethod
    def _resolve_target_hexastring(target_value: Any, target_ids: list[str]) -> int | None:
        if isinstance(target_value, int):
            raise ValueError(f"Invalid target_hexastring value: {target_value!r}")
        if isinstance(target_value, str) and target_value in target_ids:
            return target_ids.index(target_value)
        return None

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:

        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=4)

        ttk.Label(row0, text="Condition:").pack(side=tk.LEFT, padx=(5, 5))
        cond_var = tk.StringVar(value=CONDITION_DISPLAY[0])
        ttk.Combobox(row0, textvariable=cond_var, values=CONDITION_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets["condition"] = cond_var

        # ROW 1
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=4)

        available_steps = widgets.get("_steps", [])
        jump_target_displays = [
            f"{str(i + 1).zfill(2)}.  -  #{s.step_id}  - {C_STEP_TYPE_TO_LABELS.get(s.step_type, s.step_type.value)}"
            for i, s in enumerate(available_steps)
        ]
        jump_target_ids = [s.step_id for s in available_steps]
        widgets["_jump_target_displays"] = jump_target_displays
        widgets["_jump_target_ids"] = jump_target_ids
        default_target = jump_target_displays[0] if jump_target_displays else ""
        target_var = tk.StringVar(value=default_target)

        ttk.Label(row1, text="Étape cible:").pack(side=tk.LEFT, padx=(5, 5))
        ttk.Combobox(row1, textvariable=target_var, values=jump_target_displays, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets["target_hexastring"] = target_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        cond_model = params.get("condition", "success")
        widgets["condition"].set(CONDITION_MODEL_TO_VIEW.get(cond_model, CONDITION_DISPLAY[0]))
        jump_target_displays = widgets.get("_jump_target_displays", [])
        jump_target_ids = widgets.get("_jump_target_ids", [])
        target_value = params.get("target_hexastring", "")
        target_idx = self._resolve_target_hexastring(target_value, jump_target_ids)
        if target_idx is None and jump_target_displays:
            target_idx = 0
        if target_idx is not None and jump_target_displays:
            widgets["target_hexastring"].set(jump_target_displays[target_idx])

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        cond_display = widgets["condition"].get()
        target_display = widgets["target_hexastring"].get()
        jump_target_displays = widgets.get("_jump_target_displays", [])
        jump_target_ids = widgets.get("_jump_target_ids", [])
        target_idx = jump_target_displays.index(target_display) if target_display in jump_target_displays else None
        target_id = (
            jump_target_ids[target_idx] if target_idx is not None and target_idx < len(jump_target_ids) else ""
        )
        return {
            "condition": CONDITION_VIEW_TO_MODEL.get(cond_display, "success"),
            "target_hexastring": target_id,
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        target_display = widgets.get("target_hexastring", tk.StringVar()).get()
        jump_target_displays = widgets.get("_jump_target_displays", [])
        if target_display not in jump_target_displays:
            errors.append("L'étape cible sélectionnée est invalide.")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        target_hexastr = model.params.get("target_hexastring", "??")

        str_target_idx = "??"
        for target_idx, step_item in enumerate(model.parent_context):
            if step_item.step_id == target_hexastr:
                str_target_idx = f"{target_idx + 1}".zfill(2)
                break

        if str_target_idx == "??":
            target_hexastr = "???"

        cond = model.params.get("condition", "success")
        if cond == "success":
            return f"Si le résultat est un succès\nSe rendre à l'étape {str_target_idx}.  #{target_hexastr}"
        if cond == "failure":
            return f"Si le résultat est un échec\nSe rendre à l'étape {str_target_idx}.  #{target_hexastr}"
        return f"Si le résultat est un succès/échec\nToujours aller à l'étape {str_target_idx}.  #{target_hexastr}"


register_form(JumpToStepFormDef())
