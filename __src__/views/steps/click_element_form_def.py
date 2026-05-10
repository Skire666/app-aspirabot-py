"""IStepFormDef for CLICK_ELEMENT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.step_registry import register_form
from views.steps._constants import CLICK_MODES

from __src__.shared.i18n_fra import C_STEP_TYPE_TO_LABELS

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"


class ClickElementFormDef(IStepFormDef):
    """Form definition for the click element scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.CLICK_ELEMENT

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.CLICK_ELEMENT)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
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

        ttk.Label(row1, text="Type de clic à utiliser (est cumulatif) : ").pack(side=tk.LEFT, padx=(5, 5))
        mode_var = tk.StringVar(value="Normal")
        ttk.Combobox(row1, textvariable=mode_var, values=CLICK_MODES, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets["click_mode"] = mode_var

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["selector"].set(model.params.get("selector", C_INPUT_DEFAULT_CSS_SELECTOR))
        widgets["click_mode"].set(model.params.get("click_mode", "Normal"))

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "selector": widgets["selector"].get().strip(),
            "click_mode": widgets["click_mode"].get(),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        if not widgets.get("selector", tk.StringVar()).get().strip():
            errors.append("Sélecteur CSS : valeur obligatoire.")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        selector = model.params.get("selector", "<vide>")
        return f"Cliquer sur un élément\nSél. {selector}"


register_form(ClickElementFormDef())
