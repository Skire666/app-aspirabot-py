"""IStepFormDef for SCROLL_DOWN."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget


class ScrollDownFormDef(IStepFormDef):
    """Form definition for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.SCROLL_DOWN

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.SCROLL_DOWN)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Pixels:").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 4))
        pixels_var = tk.StringVar(value="1000")
        ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=pixels_var, width=10).grid(
            row=0, column=1, sticky="w", padx=(0, 4), pady=(0, 4)
        )
        widgets["pixels"] = pixels_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["pixels"].set(str(model.params.get("pixels", 1000)))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {"pixels": safe_int_widget(widgets, "pixels", 1000)}

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        if safe_int_widget(widgets, "pixels", -1) <= 0:
            return ["Pixels : doit être >= 1"]
        return []

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        return f"Défilement vers le bas\nLongueur: {model.params.get('pixels', 0)} px"


register_form(ScrollDownFormDef())
