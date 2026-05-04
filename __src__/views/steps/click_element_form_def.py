"""IStepFormDef for CLICK_ELEMENT."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.step_registry import register_form
from views.steps._constants import CLICK_MODES


class ClickElementFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.CLICK_ELEMENT

    @classmethod
    def label(cls) -> str:
        return "Cliquer sur un élément"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        sel_var = tk.StringVar()
        ttk.Entry(frame, textvariable=sel_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        widgets["selector"] = sel_var

        ttk.Label(frame, text="Mode de clic:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value="Normal")
        ttk.Combobox(frame, textvariable=mode_var, values=CLICK_MODES, state="readonly").grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        widgets["click_mode"] = mode_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["selector"].set(params.get("selector", ""))
        widgets["click_mode"].set(params.get("click_mode", "Normal"))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "selector": widgets["selector"].get().strip(),
            "click_mode": widgets["click_mode"].get(),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Le sélecteur CSS est obligatoire.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        return f"Cliquer sur un élément\nSél. : {params.get('selector', '')}"


register_form(ClickElementFormDef())
