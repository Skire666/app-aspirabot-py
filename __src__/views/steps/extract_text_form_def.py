"""IStepFormDef for EXTRACT_TEXT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    EXTRACT_MODE_DISPLAY,
    EXTRACT_MODE_MODEL_TO_VIEW,
    EXTRACT_MODE_VIEW_TO_MODEL,
    EXTRACT_TARGET_DISPLAY,
    EXTRACT_TARGET_MODEL_TO_VIEW,
    EXTRACT_TARGET_VIEW_TO_MODEL,
)

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"


class ExtractTextFormDef(IStepFormDef):
    """Form definition for the extract text scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.EXTRACT_TEXT

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.EXTRACT_TEXT)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 4))

        ttk.Label(row0, text="Sélecteur CSS : ").pack(side=tk.LEFT, padx=(0, 4))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row0, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 4))
        widgets["selector"] = sel_var

        # ROW 1
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 4))

        ttk.Label(row1, text="Mode d'extraction : ").pack(side=tk.LEFT, padx=(0, 4))
        mode_var = tk.StringVar(value=EXTRACT_MODE_DISPLAY[0])
        ttk.Combobox(row1, textvariable=mode_var, values=EXTRACT_MODE_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 4)
        )
        widgets["extract_mode"] = mode_var

        # ROW 2
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 4))

        ttk.Label(row2, text="Cible : ").pack(side=tk.LEFT, padx=(0, 4))
        target_var = tk.StringVar(value=EXTRACT_TARGET_DISPLAY[0])
        ttk.Combobox(row2, textvariable=target_var, values=EXTRACT_TARGET_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 4)
        )
        widgets["target"] = target_var

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["selector"].set(model.params.get("selector", ""))
        widgets["extract_mode"].set(
            EXTRACT_MODE_MODEL_TO_VIEW.get(model.params.get("extract_mode", "innerText"), EXTRACT_MODE_DISPLAY[0])
        )
        widgets["target"].set(
            EXTRACT_TARGET_MODEL_TO_VIEW.get(model.params.get("target", "first"), EXTRACT_TARGET_DISPLAY[0])
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "selector": widgets["selector"].get().strip(),
            "extract_mode": EXTRACT_MODE_VIEW_TO_MODEL.get(widgets["extract_mode"].get(), "innerText"),
            "target": EXTRACT_TARGET_VIEW_TO_MODEL.get(widgets["target"].get(), "first"),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Sélecteur CSS : valeur obligatoire")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        selector = model.params.get("selector", "<vide>")
        extract_mode = model.params.get("extract_mode", "")
        target = model.params.get("target", "")
        return f"Extraire contenu textuel\nSél. : {selector}  -  {extract_mode}  /  {target}"


register_form(ExtractTextFormDef())
