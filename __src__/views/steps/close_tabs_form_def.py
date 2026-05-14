"""IStepFormDef for CLOSE_TABS."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import C_MAXIMUM_NBR_TABS_BROWSER
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_FILTER_MODE: str = "<<URL>>"
C_INPUT_IS_FILTER_CUSTOM: str = "<<CUSTOM>>"
C_INPUT_DEFAULT_MAX_TABS: int = 1

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class CloseTabsFormDef(IStepFormDef):
    """Form definition for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLOSE_TABS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_CLOSE_TABS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # ROW 0
        self._build_subform_filters(frame, widgets)

        # ROW 1
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Max. onglets ouverts:").pack(side="left", padx=(0, 5))
        max_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MAX_TABS))
        ttk.Spinbox(row1, from_=1, to=C_MAXIMUM_NBR_TABS_BROWSER, textvariable=max_var, width=7).pack(
            side="left", padx=(0, 5)
        )
        widgets["max_tabs"] = max_var

        # ROW 3 — comment
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))
        ttk.Label(row3, text="Commentaire :").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @staticmethod
    def _build_subform_filters(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Creates the URL input field."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        filter_mode_var = tk.StringVar(value=C_INPUT_DEFAULT_FILTER_MODE)
        filter_url_var = tk.StringVar(value=".com")

        # Mode selection.
        CloseTabsFormDef._build_url_mode_buttons(line1, filter_mode_var)

        filter_url_entry = ttk.Entry(line1, textvariable=filter_url_var)
        filter_url_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["filter_mode"] = filter_mode_var  # '<<URL>>' or '<<CUSTOM>>'
        widgets["filter_custom"] = filter_url_var

        # Keep the entry state in sync with the selected mode.
        CloseTabsFormDef._bind_url_mode_entry(filter_mode_var, filter_url_entry)

    @staticmethod
    def _build_url_mode_buttons(line1: ttk.Frame, filter_mode_var: tk.StringVar) -> None:
        """Creates the URL mode radio buttons."""
        # URL source selection.
        tk.Radiobutton(
            line1,
            text="Garder l'URL d'origine",
            variable=filter_mode_var,
            value="<<URL>>",
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            line1,
            text="Filtre contenant",
            variable=filter_mode_var,
            value="<<CUSTOM>>",
        ).pack(side=tk.LEFT, padx=(0, 5))

    @staticmethod
    def _bind_url_mode_entry(filter_mode_var: tk.StringVar, filter_url_entry: ttk.Entry) -> None:
        """Synchronizes the URL entry state with mode selection."""

        def _sync_url_entry_state(*_args: object) -> None:
            state = "readonly" if filter_mode_var.get() == "<<URL>>" else "normal"
            filter_url_entry.configure(state=state)

        # React to mode changes and initialize the current state.
        filter_mode_var.trace_add("write", _sync_url_entry_state)
        _sync_url_entry_state()

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["filter_mode"].set(model.params.get("filter_mode", "<<URL>>"))
        widgets["filter_custom"].set(model.params.get("filter_custom", ""))
        widgets["max_tabs"].set(str(model.params.get("max_tabs", C_INPUT_DEFAULT_MAX_TABS)))
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "filter_mode": widgets["filter_mode"].get(),
            "filter_custom": widgets["filter_custom"].get().strip(),
            "max_tabs": safe_int_widget(widgets, "max_tabs", C_INPUT_DEFAULT_MAX_TABS),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []

        filter_mode = widgets["filter_mode"].get()
        filter_custom = widgets["filter_custom"].get().strip()

        max_tb = safe_int_widget(widgets, "max_tabs", -1)

        if filter_mode == C_INPUT_IS_FILTER_CUSTOM and not filter_custom:
            errors.append("Le filtre URL est obligatoire.")
        if max_tb <= 0:
            errors.append("Nombre max. d'onglets : doit être >= 1")
        return errors

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        max_tabs = model.params.get("max_tabs", C_INPUT_DEFAULT_MAX_TABS)

        # si mode "<<CUSTOM>>"
        if model.params.get("filter_mode") == C_INPUT_IS_FILTER_CUSTOM:
            filter_custom = model.params.get("filter_custom", "")
            return f"Fermer les onglets  -  {max_tabs} onglet(s) max.\nFiltre URL : *{filter_custom}*"
        # si mode "<<URL>>"
        return f"Fermer les onglets  -  {max_tabs} onglet(s) max.\nFiltre : Garde l'URL de départ."


register_form(CloseTabsFormDef())
