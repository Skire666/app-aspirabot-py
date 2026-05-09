"""IStepFormDef for EXTRACT_TEXT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.step_registry import register_form
from views.steps._constants import (
    EXTRACT_MODE_DISPLAY,
    EXTRACT_MODE_MODEL_TO_VIEW,
    EXTRACT_MODE_VIEW_TO_MODEL,
    EXTRACT_TARGET_DISPLAY,
    EXTRACT_TARGET_MODEL_TO_VIEW,
    EXTRACT_TARGET_VIEW_TO_MODEL,
)

from __src__.shared.i18n_fra import C_STEP_TYPE_TO_LABELS

C_INPUT_DEFAULT_CSS_SELECTOR = "<div class='ds-theme' >> div.ds-theme   ||  id='header' >> #header  ||  ou sinon copy selector dans chrome/debug"


class ExtractTextFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.EXTRACT_TEXT

    @classmethod
    def label(cls) -> str:
        return C_STEP_TYPE_TO_LABELS.get(StepType.EXTRACT_TEXT)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:

        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=4)

        ttk.Label(row0, text="Sélecteur CSS : ").pack(side=tk.LEFT, padx=(5, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row0, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["selector"] = sel_var

        # ROW 1
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=4)

        ttk.Label(row1, text="Mode d'extraction : ").pack(side=tk.LEFT, padx=(5, 5))
        mode_var = tk.StringVar(value=EXTRACT_MODE_DISPLAY[0])
        ttk.Combobox(row1, textvariable=mode_var, values=EXTRACT_MODE_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets["extract_mode"] = mode_var

        # ROW 2
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=4)

        ttk.Label(row2, text="Cible : ").pack(side=tk.LEFT, padx=(5, 5))
        target_var = tk.StringVar(value=EXTRACT_TARGET_DISPLAY[0])
        ttk.Combobox(row2, textvariable=target_var, values=EXTRACT_TARGET_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets["target"] = target_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["selector"].set(params.get("selector", ""))
        widgets["extract_mode"].set(
            EXTRACT_MODE_MODEL_TO_VIEW.get(params.get("extract_mode", "innerText"), EXTRACT_MODE_DISPLAY[0])
        )
        widgets["target"].set(
            EXTRACT_TARGET_MODEL_TO_VIEW.get(params.get("target", "first"), EXTRACT_TARGET_DISPLAY[0])
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "selector": widgets["selector"].get().strip(),
            "extract_mode": EXTRACT_MODE_VIEW_TO_MODEL.get(widgets["extract_mode"].get(), "innerText"),
            "target": EXTRACT_TARGET_VIEW_TO_MODEL.get(widgets["target"].get(), "first"),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Sélecteur CSS : valeur obligatoire")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        selector = model.params.get("selector", "<vide>")
        extract_mode = model.params.get("extract_mode", "")
        target = model.params.get("target", "")
        return f"Extraire contenu textuel\nSél. : {selector}  -  {extract_mode}  /  {target}"


register_form(ExtractTextFormDef())
