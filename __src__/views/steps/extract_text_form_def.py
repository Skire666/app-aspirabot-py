"""IStepFormDef for EXTRACT_TEXT."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.step_registry import register_form
from views.steps._constants import (
    EXTRACT_MODE_DISPLAY, EXTRACT_MODE_MODEL_TO_VIEW, EXTRACT_MODE_VIEW_TO_MODEL,
    EXTRACT_TARGET_DISPLAY, EXTRACT_TARGET_MODEL_TO_VIEW, EXTRACT_TARGET_VIEW_TO_MODEL,
)


class ExtractTextFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.EXTRACT_TEXT

    @classmethod
    def label(cls) -> str:
        return "Extraire contenu textuel"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(frame, textvariable=sel_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        widgets["selector"] = sel_var

        ttk.Label(frame, text="Mode d'extraction:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value=EXTRACT_MODE_DISPLAY[0])
        ttk.Combobox(frame, textvariable=mode_var, values=EXTRACT_MODE_DISPLAY, state="readonly").grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        widgets["extract_mode"] = mode_var

        ttk.Label(frame, text="Cible:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        target_var = tk.StringVar(value=EXTRACT_TARGET_DISPLAY[0])
        ttk.Combobox(frame, textvariable=target_var, values=EXTRACT_TARGET_DISPLAY, state="readonly").grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        widgets["target"] = target_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["selector"].set(params.get("selector", ""))
        widgets["extract_mode"].set(EXTRACT_MODE_MODEL_TO_VIEW.get(params.get("extract_mode", "innerText"), EXTRACT_MODE_DISPLAY[0]))
        widgets["target"].set(EXTRACT_TARGET_MODEL_TO_VIEW.get(params.get("target", "first"), EXTRACT_TARGET_DISPLAY[0]))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "selector": widgets["selector"].get().strip(),
            "extract_mode": EXTRACT_MODE_VIEW_TO_MODEL.get(widgets["extract_mode"].get(), "innerText"),
            "target": EXTRACT_TARGET_VIEW_TO_MODEL.get(widgets["target"].get(), "first"),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Le sélecteur CSS est obligatoire.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        selector = params.get("selector", "")
        extract_mode = params.get("extract_mode", "")
        target = params.get("target", "")
        return f"Extraire contenu textuel\nSél. : {selector} [{extract_mode} / {target}]"


register_form(ExtractTextFormDef())
