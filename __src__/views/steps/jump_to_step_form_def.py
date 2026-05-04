"""IStepFormDef for JUMP_TO_STEP."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.step_registry import register_form
from views.steps._constants import CONDITION_DISPLAY, CONDITION_MODEL_TO_VIEW, CONDITION_VIEW_TO_MODEL

_STEP_LABELS: dict[StepType, str] = {
    StepType.OPEN_URL: "Ouvrir une URL",
    StepType.REFRESH_PAGE: "Rafraîchir la page",
    StepType.SLEEP_X_TIME: "Attendre une durée fixe",
    StepType.RANDOM_PAUSE: "Attendre aléatoirement",
    StepType.DOWNLOAD_IMAGE: "Télécharger les images",
    StepType.WAIT_IMAGE_SIZE: "Vérifier une taille d'image",
    StepType.WAIT_ELEMENT: "Vérifier les éléments",
    StepType.COUNT_ELEMENT: "Compter les éléments",
    StepType.CLICK_ELEMENT: "Cliquer sur un élément",
    StepType.SCROLL_DOWN: "Défiler vers le bas",
    StepType.EXTRACT_TEXT: "Extraire contenu textuel",
    StepType.JUMP_TO_STEP: "Si OK/KO, se rendre à ...",
    StepType.CLOSE_TABS: "Fermer des onglets",
    StepType.END_PROCESS: "Fin du processus",
    StepType.WAIT_USER_ACTION: "Attendre action utilisateur",
}


class JumpToStepFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.JUMP_TO_STEP

    @classmethod
    def label(cls) -> str:
        return "Si l'étape d'avant est un ..."

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Condition:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        cond_var = tk.StringVar(value=CONDITION_DISPLAY[0])
        ttk.Combobox(frame, textvariable=cond_var, values=CONDITION_DISPLAY, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        widgets["condition"] = cond_var

        available_steps = widgets.get("_steps", [])  ## list StepScrapingModel
        jump_target_displays = [
            f"Étape {i + 1}  -  #{s.step_id}  - {_STEP_LABELS.get(s.step_type, s.step_type.value)}"
            for i, s in enumerate(available_steps)
        ]
        widgets["_jump_target_displays"] = jump_target_displays
        default_target = jump_target_displays[0] if jump_target_displays else ""
        target_var = tk.StringVar(value=default_target)
        ttk.Label(frame, text="Étape cible:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ttk.Combobox(frame, textvariable=target_var, values=jump_target_displays, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        widgets["target_index"] = target_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        cond_model = params.get("condition", "success")
        widgets["condition"].set(CONDITION_MODEL_TO_VIEW.get(cond_model, CONDITION_DISPLAY[0]))
        target_idx = params.get("target_index", 0)
        jump_target_displays = widgets.get("_jump_target_displays", [])
        if 0 <= target_idx < len(jump_target_displays):
            widgets["target_index"].set(jump_target_displays[target_idx])
        elif jump_target_displays:
            widgets["target_index"].set(jump_target_displays[0])

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        cond_display = widgets["condition"].get()
        target_display = widgets["target_index"].get()
        jump_target_displays = widgets.get("_jump_target_displays", [])
        target_idx = jump_target_displays.index(target_display) if target_display in jump_target_displays else 0
        return {
            "condition": CONDITION_VIEW_TO_MODEL.get(cond_display, "success"),
            "target_index": target_idx,
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        target_display = widgets.get("target_index", tk.StringVar()).get()
        jump_target_displays = widgets.get("_jump_target_displays", [])
        if target_display not in jump_target_displays:
            errors.append("L'étape cible sélectionnée est invalide.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        target = params.get("target_index", 0)
        cond = params.get("condition", "success")
        next_step = str(target + 1).zfill(2)
        if cond == "success":
            return f"Si l'étape d'avant est ...\nun succès, se rendre à l'étape [{next_step}]"
        if cond == "failure":
            return f"Si l'étape d'avant est ...\nun échec, se rendre à l'étape [{next_step}]"
        return f"Toujour sauter à ...\nl'étape {next_step}"


register_form(JumpToStepFormDef())
