"""IStepFormDef for SCROLL_DOWN."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget


class ScrollDownFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.SCROLL_DOWN

    @classmethod
    def label(cls) -> str:
        return "Défiler vers le bas"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Pixels:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        pixels_var = tk.StringVar(value="1000")
        ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=pixels_var, width=10).grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        widgets["pixels"] = pixels_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["pixels"].set(str(params.get("pixels", 1000)))

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {"pixels": safe_int_widget(widgets, "pixels", 1000)}

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        return []

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        return f"Défilement vers le bas\nLongueur: {model.params.get('pixels', 0)} px"


register_form(ScrollDownFormDef())
