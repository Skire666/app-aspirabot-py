"""IStepFormDef for CLOSE_TABS."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_MAXIMUM_NBR_TABS_BROWSER
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_URL_FILTER: str = "<<URL>>"
C_INPUT_DEFAULT_MAX_TABS: int = 1

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class CloseTabsFormDef(IStepFormDef):
    """Form definition for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.CLOSE_TABS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.CLOSE_TABS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Garder uniquement ce qui contient : ").pack(side="left", padx=(0, 5))
        filter_var = tk.StringVar(value=C_INPUT_DEFAULT_URL_FILTER)
        ttk.Entry(row0, textvariable=filter_var).pack(side="left", padx=(0, 5))
        widgets["url_filter"] = filter_var

        ttk.Label(row0, text="<<URL>> ou bien .com").pack(side="left", padx=(0, 5))

        # ROW 1
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Max. onglets ouverts:").pack(side="left", padx=(0, 5))
        max_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MAX_TABS))
        ttk.Spinbox(row1, from_=0, to=C_MAXIMUM_NBR_TABS_BROWSER, textvariable=max_var, width=7).pack(
            side="left", padx=(0, 5)
        )
        widgets["max_tabs"] = max_var

        # ROW 3 — comment
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))
        ttk.Label(row3, text="Commentaire : ").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["url_filter"].set(model.params.get("url_filter", C_INPUT_DEFAULT_URL_FILTER))
        widgets["max_tabs"].set(str(model.params.get("max_tabs", C_INPUT_DEFAULT_MAX_TABS)))
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "url_filter": widgets["url_filter"].get().strip(),
            "max_tabs": safe_int_widget(widgets, "max_tabs", C_INPUT_DEFAULT_MAX_TABS),
            "comment": widgets["comment"].get().strip(),
        }

    @override
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

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        max_tabs = model.params.get("max_tabs", C_INPUT_DEFAULT_MAX_TABS)
        url_filter = model.params.get("url_filter", C_INPUT_DEFAULT_URL_FILTER)
        if max_tabs == 0:
            return "Fermer tous les onglets\nIl ne restera aucun onglet d'ouvert"

        # si plusieurs
        label = f"Fermer les onglets  -  {max_tabs} onglet(s) max.\n"
        label += f"Ne garder que les URL avec '{url_filter}'"
        return label


register_form(CloseTabsFormDef())
