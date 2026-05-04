"""IStepFormDef for REFRESH_PAGE."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox


class RefreshPageFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.REFRESH_PAGE

    @classmethod
    def label(cls) -> str:
        return "Rafraîchir la page"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        cache_var = tk.BooleanVar(value=False)
        CanvasCheckbox(frame, text="Vider le cache", variable=cache_var).grid(row=0, column=0, sticky="w", padx=5, pady=4)
        widgets["clear_cache"] = cache_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["clear_cache"].set(bool(params.get("clear_cache", False)))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {"clear_cache": bool(widgets["clear_cache"].get())}

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        return []

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        if params.get("clear_cache"):
            return "Rafraîchir la page\nVide le cache (Ctrl+F5)"
        return "Rafraîchir la page\nGarde le cache (F5)"


register_form(RefreshPageFormDef())
