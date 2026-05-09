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
        return C_STEP_TYPE_TO_LABELS.get(StepType.JUMP_TO_STEP)

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

        available_steps: list[StepScrapingModel] = widgets.get("_all_steps_available", [])

        # liste des étapes disponibles pour la cible du saut, au format d'affichage dans la combobox : "01. - #hexastring - label"
        all_targets_display = []
        for index, s in enumerate(available_steps):
            all_targets_display.append(
                f"{str(index + 1).zfill(2)}.  -  #{s.step_id}  - {C_STEP_TYPE_TO_LABELS.get(s.step_type, s.step_type.value)}"
            )
        widgets["_all_targets_display"] = all_targets_display

        ## list of targethexastring
        all_targets_hexastring = [s.step_id for s in available_steps]
        widgets["_all_targets_hexastring"] = all_targets_hexastring

        ## étape cible par défaut : la première de la liste des étapes disponibles
        widgets["_choice_target_hexastring"] = available_steps[0].step_id if available_steps else ""
        widgets["_choice_target_display"] = all_targets_display[0] if all_targets_display else ""

        # GUI
        target_var = tk.StringVar(value=widgets["_choice_target_display"])

        ttk.Label(row1, text="Étape cible:").pack(side=tk.LEFT, padx=(5, 5))
        ttk.Combobox(row1, textvariable=target_var, values=all_targets_display, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        print(f"AA) Target value: {widgets['_choice_target_hexastring']!r}")

    def load_params_step_to_widget(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        # consition
        cond_model = params.get("condition", "success")
        widgets["condition"].set(CONDITION_MODEL_TO_VIEW.get(cond_model, CONDITION_DISPLAY[0]))

        # cible du JUMP_TO_STEP

        all_targets_display = widgets.get("_all_targets_display", [])
        all_targets_hexastring = widgets.get("_all_targets_hexastring", [])
        target_hexastring = params.get("target_hexastring", "")

        if target_hexastring is not None and target_hexastring in all_targets_hexastring:
            widgets["_choice_target_hexastring"] = target_hexastring
            index = all_targets_hexastring.index(target_hexastring)
            widgets["_choice_target_display"] = all_targets_display[index]
        else:
            widgets["_choice_target_hexastring"] = ""
            widgets["_choice_target_display"] = ""

    ## le dictionne qui est retourné, c'est les '.params' du StepScrapingModel
    # il doit contenir la condition et la cible du saut (hexastring de l'étape cible)
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        cond_display = widgets["condition"].get()

        target_hexastring = widgets.get("_choice_target_hexastring", "")
        print(f"CC) target_hexastring : {target_hexastring!r}")
        return {
            "condition": CONDITION_VIEW_TO_MODEL.get(cond_display, "success"),
            "target_hexastring": target_hexastring,
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        choice_target_hexastring = widgets.get("_choice_target_hexastring", "??")
        all_targets_hexastring = widgets.get("_all_targets_hexastring", [])
        print(f"DD) target_hexastring : {choice_target_hexastring!r}")

        # si vide ou "????" (valeur par défaut d'une cible non trouvée), c'est une erreur obligatoire
        if not choice_target_hexastring:
            return ["L'étape cible : valeur obligatoire"]
        # si n'existe pas dans la liste des cibles possibles, c'est une erreur
        if choice_target_hexastring not in all_targets_hexastring:
            return [f"L'étape cible '#{choice_target_hexastring}' : doit être valide"]
        return []

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        target_hexastring = model.params.get("target_hexastring", "????")

        str_target_index = ""
        for index_target, step_item in enumerate(model.parent_context):
            if step_item.step_id == target_hexastring:
                str_target_index = f"{index_target + 1}".zfill(2)
                break

        if not str_target_index:
            target_hexastring = "????"
            str_target_index = "??"

        cond = model.params.get("condition", "success")
        if cond == "success":
            return f"Si le résultat est un succès\nSe rendre à l'étape {str_target_index}.  #{target_hexastring}"
        if cond == "failure":
            return f"Si le résultat est un échec\nSe rendre à l'étape {str_target_index}.  #{target_hexastring}"
        return f"Si le résultat est un succès/échec\nToujours aller à l'étape {str_target_index}.  #{target_hexastring}"


register_form(JumpToStepFormDef())
