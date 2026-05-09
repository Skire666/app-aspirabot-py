"""IStepFormDef for CLOSE_TABS."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_MAXIMUM_NBR_TABS_BROWSER
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget

from __src__.shared.i18n_fra import C_STEP_TYPE_TO_LABELS

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

C_INPUT_DEFAULT_URL_FILTER: str = "<<URL>>"
C_INPUT_DEFAULT_MAX_TABS: int = 1

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class CloseTabsFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.CLOSE_TABS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.CLOSE_TABS)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Garder uniquement ce qui contient : ").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        filter_var = tk.StringVar(value=C_INPUT_DEFAULT_URL_FILTER)
        ttk.Entry(frame, textvariable=filter_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        widgets["url_filter"] = filter_var

        ttk.Label(frame, text="<<URL>> ou bien .com").grid(row=1, column=1, sticky="w", padx=5, pady=(0, 4))

        ttk.Label(frame, text="Max. onglets ouverts:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        max_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MAX_TABS))
        ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_NBR_TABS_BROWSER, textvariable=max_var, width=7).grid(
            row=2, column=1, sticky="w", padx=5, pady=4
        )
        widgets["max_tabs"] = max_var

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["url_filter"].set(model.params.get("url_filter", C_INPUT_DEFAULT_URL_FILTER))
        widgets["max_tabs"].set(str(model.params.get("max_tabs", C_INPUT_DEFAULT_MAX_TABS)))

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "url_filter": widgets["url_filter"].get().strip(),
            "max_tabs": safe_int_widget(widgets, "max_tabs", C_INPUT_DEFAULT_MAX_TABS),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        url = widgets["url_filter"].get().strip()
        max_tb = safe_int_widget(widgets, "max_tabs", -1)

        if max_tb <= 0:
            errors.append("Nombre max. d'onglets : doit être >= 1")
        if not url:
            errors.append("Filtre URL : valeur obligatoire")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        max_tabs = model.params.get("max_tabs", C_INPUT_DEFAULT_MAX_TABS)
        url_filter = model.params.get("url_filter", C_INPUT_DEFAULT_URL_FILTER)
        if max_tabs == 0:
            return "Fermer tous les onglets\nIl ne restera aucun onglet d'ouvert"

        ## si plusieurs
        label = f"Fermer les onglets  -  {max_tabs} onglet(s) max.\n"
        label += f"Ne garder que les URL contenant '{url_filter}'"
        return label


register_form(CloseTabsFormDef())
