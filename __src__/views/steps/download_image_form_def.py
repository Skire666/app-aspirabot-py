"""IStepFormDef for DOWNLOAD_IMAGE."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import DOWNLOAD_MODES, safe_int_widget


def _add_dimension_row(frame: ttk.Frame, widgets: dict[str, Any], row: int, label: str, min_key: str, max_key: str, default_min: int, default_max: int) -> None:
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(frame, text="Min:").grid(row=row, column=1, sticky="w", padx=2)
    min_var = tk.StringVar(value=str(default_min))
    ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=min_var, width=8).grid(row=row, column=2, padx=5, pady=4)
    ttk.Label(frame, text="Max:").grid(row=row, column=3, sticky="w", padx=2)
    max_var = tk.StringVar(value=str(default_max))
    ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=max_var, width=8).grid(row=row, column=4, padx=5, pady=4)
    widgets[min_key] = min_var
    widgets[max_key] = max_var


class DownloadImageFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.DOWNLOAD_IMAGE

    @classmethod
    def label(cls) -> str:
        return "Télécharger les images"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(2, weight=1)
        ttk.Label(frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        mode_var = tk.StringVar(value="largest")
        ttk.Combobox(frame, textvariable=mode_var, values=DOWNLOAD_MODES, state="readonly").grid(row=0, column=1, columnspan=4, sticky="ew", padx=5, pady=4)
        widgets["mode"] = mode_var
        unique_var = tk.BooleanVar(value=False)
        CanvasCheckbox(frame, text="Télécharger les images uniques (mode 'aucun doublon')", variable=unique_var).grid(row=1, column=0, columnspan=5, sticky="w", padx=5, pady=(0, 4))
        widgets["unique_only"] = unique_var
        _add_dimension_row(frame, widgets, 2, "Hauteur (px):", "height_min", "height_max", 0, C_MAXIMUM_SIZE_IMAGE)
        _add_dimension_row(frame, widgets, 3, "Largeur (px):", "width_min", "width_max", 0, C_MAXIMUM_SIZE_IMAGE)

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["mode"].set(params.get("mode", "largest"))
        widgets["unique_only"].set(bool(params.get("unique_only", False)))
        widgets["height_min"].set(str(params.get("height_min", 0)))
        widgets["height_max"].set(str(params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["width_min"].set(str(params.get("width_min", 0)))
        widgets["width_max"].set(str(params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": widgets["mode"].get(),
            "unique_only": bool(widgets["unique_only"].get()),
            "height_min": safe_int_widget(widgets, "height_min", 0),
            "height_max": safe_int_widget(widgets, "height_max", C_MAXIMUM_SIZE_IMAGE),
            "width_min": safe_int_widget(widgets, "width_min", 0),
            "width_max": safe_int_widget(widgets, "width_max", C_MAXIMUM_SIZE_IMAGE),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if safe_int_widget(widgets, key, -1) < 0:
                errors.append(f"La valeur '{key}' doit être un entier positif ou égal à 0.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        mode = params.get("mode", "")
        unique_only = params.get("unique_only", False)
        width_min = params.get("width_min", 0)
        height_min = params.get("height_min", 0)
        width_max = params.get("width_max", 0)
        height_max = params.get("height_max", 0)
        dup_str = "(doublons refusés)" if unique_only else "(tout est pris)"
        return f"Télécharger les images\n{mode} - {dup_str} - {width_min}x{height_min} -> {width_max}x{height_max}"


register_form(DownloadImageFormDef())
