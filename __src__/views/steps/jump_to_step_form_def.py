"""IStepFormDef for JUMP_TO_STEP."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import CONDITION_DISPLAY, CONDITION_MODEL_TO_VIEW, CONDITION_VIEW_TO_MODEL

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class JumpToStepFormDef(IStepFormDef):
    """Form definition for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.JUMP_TO_STEP

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.JUMP_TO_STEP)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Condition:").pack(side=tk.LEFT, padx=(0, 5))
        cond_var = tk.StringVar(value=CONDITION_DISPLAY[0])
        ttk.Combobox(row0, textvariable=cond_var, values=CONDITION_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets["condition"] = cond_var

        # ROW 1
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        available_steps: list[StepScrapingModel] = widgets.get("_all_steps_available", [])

        # liste des étapes disponibles pour la cible du saut
        # au format d'affichage dans la combobox : "01. - #hexastring - label"
        all_choices_listbox = []
        all_steps_id_to_index = []
        all_hexastring_to_model = {}
        for index, s in enumerate(available_steps):
            choice_str = self.compute_string_displayed_in_combobox(index, s)
            all_choices_listbox.append(choice_str)
            all_steps_id_to_index.append(s.step_id)
            all_hexastring_to_model[s.step_id] = s
        widgets["_all_choices_listbox"] = all_choices_listbox
        widgets["_all_steps_id_to_index"] = all_steps_id_to_index
        widgets["_all_hexastring_to_model"] = all_hexastring_to_model

        default_choice = all_choices_listbox[0] if all_choices_listbox else ""

        # GUI
        print(f"A) {datetime.now()} default_choice = {default_choice!r}")

        target_var = tk.StringVar(value=default_choice)
        widgets["_choice_from_listbox"] = target_var  # important de passer le stringvar

        ttk.Label(row1, text="Étape cible:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(row1, textvariable=target_var, values=all_choices_listbox, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )

        # ROW 2 — comment
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Commentaire : ").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    # à partir du model, alimente view
    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        # consition
        cond_model = model.params.get("condition", "success")
        widgets["condition"].set(CONDITION_MODEL_TO_VIEW.get(cond_model, CONDITION_DISPLAY[0]))

        # cible du JUMP_TO_STEP
        all_hexastring_to_model = widgets.get("_all_hexastring_to_model", [])
        all_choices_listbox = widgets.get("_all_choices_listbox", [])
        target_hexastring = model.params.get("target_hexastring", "")

        choice_str = all_choices_listbox[0] if all_choices_listbox else ""

        if target_hexastring is not None and all_choices_listbox:
            all_steps_id_to_index = widgets.get("_all_steps_id_to_index", [])
            index_target = (
                all_steps_id_to_index.index(target_hexastring) if target_hexastring in all_steps_id_to_index else -1
            )
            model_target = all_hexastring_to_model.get(target_hexastring)
            choice_str = self.compute_string_displayed_in_combobox(index_target, model_target)

        widgets["_choice_from_listbox"].set(choice_str)  # Clear selection if target is invalid.
        widgets["comment"].set(model.params.get("comment", ""))
        print(f"B) {datetime.now()} target_hexastring = {target_hexastring!r}")
        print(f"B) {datetime.now()} choice_str = {choice_str!r}")

    @staticmethod
    def compute_string_displayed_in_combobox(index: int, model: StepScrapingModel) -> str:
        """Compute the string to be displayed in the combobox based on the model parameters."""
        if index >= 0 and model is not None:
            return f"{str(index + 1).zfill(2)}.  -  #{model.step_id}  - {JumpToStepFormDef.label()}"
        return ""

    # le dictionne qui est retourné, c'est les '.params' du StepScrapingModel
    # il doit contenir la condition et la cible du saut (hexastring de l'étape cible)
    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        cond_display = widgets["condition"].get()

        choice_target_hexastring = widgets.get("_choice_from_listbox", "").get()
        hexastring = self._extract_after_hash_hexastring(choice_target_hexastring)
        print(f"C) {datetime.now()} hexastring : {hexastring!r}")
        print(f"C) {datetime.now()} choice_target_hexastring : {choice_target_hexastring!r}")
        return {
            "condition": CONDITION_VIEW_TO_MODEL.get(cond_display, "success"),
            "target_hexastring": hexastring,
            "comment": widgets["comment"].get().strip(),
        }

    @staticmethod
    def _extract_after_hash_hexastring(choice_target_hexastring: str) -> str:
        """Trouve '#' et retourne les 4 caractères suivants."""
        # Extrait l'hexastring de la sélection de la combobox
        # qui est au format "01. - #hxst - label_xxxx".
        if choice_target_hexastring is not None:
            hash_index = choice_target_hexastring.find("#")
            if hash_index != -1:
                return choice_target_hexastring[hash_index + 1 : hash_index + 5]
        return ""

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        choice_target_hexastring = widgets.get("_choice_from_listbox", "").get()
        hexastring = self._extract_after_hash_hexastring(choice_target_hexastring)

        # si vide ou "????" (valeur par défaut d'une cible non trouvée), c'est une erreur obligatoire
        if not hexastring:
            return ["L'étape cible : valeur obligatoire"]

        all_hexastring_to_model = widgets.get("_all_hexastring_to_model", {})

        print(f"D) {datetime.now()} hexastring : {hexastring!r}")
        # si n'existe pas dans la liste des cibles possibles, c'est une erreur
        if hexastring not in all_hexastring_to_model:
            return [f"L'étape cible '#{hexastring}' : doit être valide"]
        return []

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        target_hexastring = model.params.get("target_hexastring", "????")

        target_index = ""
        for index_target, step_item in enumerate(model.parent_context):
            if step_item.step_id == target_hexastring:
                target_index = f"{index_target + 1}".zfill(2)
                break

        if not target_index:
            target_hexastring = "????"
            target_index = "??"

        cond = model.params.get("condition", "success")
        if cond == "success":
            return f"Si le résultat est un succès\nSe rendre à l'étape {target_index}.  #{target_hexastring}"
        if cond == "failure":
            return f"Si le résultat est un échec\nSe rendre à l'étape {target_index}.  #{target_hexastring}"
        return f"Si le résultat est un succès/échec\nToujours aller à l'étape {target_index}.  #{target_hexastring}"


register_form(JumpToStepFormDef())
