"""IStepFormDef for CLOSE_TABS."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.constants import C_MAXIMUM_NBR_TABS_BROWSER
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget


class CloseTabsFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.CLOSE_TABS

    @classmethod
    def label(cls) -> str:
        return "Fermer les onglets"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Filtre URL:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        filter_var = tk.StringVar()
        ttk.Entry(frame, textvariable=filter_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        widgets["url_filter"] = filter_var

        ttk.Label(frame, text="(Laisser vide pour ne pas filtrer)", foreground="gray").grid(
            row=1, column=1, sticky="w", padx=5, pady=(0, 4)
        )

        ttk.Label(frame, text="Max. onglets ouverts:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        max_var = tk.StringVar(value="0")
        ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_NBR_TABS_BROWSER, textvariable=max_var, width=7).grid(
            row=2, column=1, sticky="w", padx=5, pady=4
        )
        widgets["max_tabs"] = max_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["url_filter"].set(params.get("url_filter", ""))
        widgets["max_tabs"].set(str(params.get("max_tabs", 0)))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "url_filter": widgets["url_filter"].get().strip(),
            "max_tabs": safe_int_widget(widgets, "max_tabs", 0),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        url = widgets["url_filter"].get().strip()
        max_tb = safe_int_widget(widgets, "max_tabs", -1)

        if max_tb < 0:
            errors.append("Le nombre maximum d'onglets doit être un entier positif ou égal à 0.")
        if url and max_tb == 0:
            errors.append(
                "Un filtre URL ne peut pas être utilisé si le nombre maximum d'onglets est 0 (tous les onglets seront fermés)."
            )
        if max_tb >= 1 and not url:
            errors.append(
                "Un filtre URL doit être utilisé si le nombre maximum d'onglets est supérieur ou égal à 1 (sinon, aucun onglet ne sera fermé)."
            )
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        max_tabs = params.get("max_tabs", 0)
        url_filter = params.get("url_filter", "")
        if max_tabs == 0:
            return "Fermer les onglets  -  Tous\nIl ne restera aucun onglet d'ouvert"

        ## si plusieurs
        label = f"Fermer les onglets  -  {max_tabs} onglet(s) max.\n"
        label += f"Ne garde que si contient '{url_filter}'"
        return label


register_form(CloseTabsFormDef())
