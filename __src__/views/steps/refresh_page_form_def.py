"""IStepFormDef for REFRESH_PAGE."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox


class RefreshPageFormDef(IStepFormDef):
    """Form definition for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.REFRESH_PAGE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.REFRESH_PAGE)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        cache_var = tk.BooleanVar(value=False)
        CanvasCheckbox(frame, text="Vider le cache (Ctrl + F5)", variable=cache_var).grid(row=0, column=0, sticky="w")
        widgets["clear_cache"] = cache_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["clear_cache"].set(bool(model.params.get("clear_cache", False)))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {"clear_cache": bool(widgets["clear_cache"].get())}

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        # Aucune validation nécessaire pour ce formulaire, il n'y a qu'une option booléenne.
        return []

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        if model.params.get("clear_cache"):
            return "Rafraîchir la page\nVide le cache (Ctrl+F5)"
        return "Rafraîchir la page\nGarde le cache (F5)"


register_form(RefreshPageFormDef())
