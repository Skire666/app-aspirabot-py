"""IStepFormDef for OPEN_URL."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_UNITS_TIME_ALLOWED_FOR_VIEW, C_UNITS_TIME_DEFAULT_MODEL, C_UNITS_TIME_DEFAULT_VIEW
from shared.step_registry import register_form
from views.steps._constants import WAIT_STATES, WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget


class OpenUrlFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.OPEN_URL

    @classmethod
    def label(cls) -> str:
        return "Ouvrir une URL"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="URL:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=url_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        widgets["url"] = url_var

        ttk.Label(frame, text="État d'attente:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ws_var = tk.StringVar(value="domcontentloaded")
        ttk.Combobox(frame, textvariable=ws_var, values=WAIT_STATES, state="readonly").grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        widgets["wait_state"] = ws_var

        timeout_frame = ttk.Frame(frame)
        timeout_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        ttk.Label(timeout_frame, text="Timeout").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value="0")
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        tu_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(timeout_frame, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(timeout_frame, text="(0 = désactivé)", foreground="gray").pack(side=tk.LEFT)
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["url"].set(params.get("url", ""))
        widgets["wait_state"].set(params.get("wait_state", "domcontentloaded"))
        widgets["timeout_duration"].set(str(params.get("timeout_duration", 0)))
        widgets["timeout_unit"].set(WAIT_UNIT_MODEL_TO_VIEW.get(params.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "url": widgets["url"].get().strip(),
            "wait_state": widgets["wait_state"].get(),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", 0),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not widgets.get("url", tk.StringVar()).get().strip():
            errors.append("L'URL est obligatoire.")
        if safe_int_widget(widgets, "timeout_duration", -1) < 0:
            errors.append("Durée de timeout doit être un nombre positif.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        url = params.get("url", "")
        td = params.get("timeout_duration", 0)
        tu = params.get("timeout_unit", "")
        label = f"Ouvrir une URL\n{url}"
        if td:
            label += f" [timeout: {td} {tu}]"
        return label


register_form(OpenUrlFormDef())
