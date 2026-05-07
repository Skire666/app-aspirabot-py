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

C_INPUT_DEFAULT_MINIMUM_SIZE = 200
C_INPUT_DEFAULT_MODE_DDL = DOWNLOAD_MODES[-1]  # all


def _add_dimension_row(
    frame: ttk.Frame,
    widgets: dict[str, Any],
    row: int,
    label: str,
    min_key: str,
    max_key: str,
    default_min: int,
    default_max: int,
) -> None:
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(frame, text="Min:").grid(row=row, column=1, sticky="w", padx=2)
    min_var = tk.StringVar(value=str(default_min))
    ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=min_var, width=8).grid(
        row=row, column=2, padx=5, pady=4
    )
    ttk.Label(frame, text="Max:").grid(row=row, column=3, sticky="w", padx=2)
    max_var = tk.StringVar(value=str(default_max))
    ttk.Spinbox(frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=max_var, width=8).grid(
        row=row, column=4, padx=5, pady=4
    )
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

        mode_var = tk.StringVar(value=C_INPUT_DEFAULT_MODE_DDL)
        unique_var = tk.BooleanVar(value=True)
        widgets["mode"] = mode_var
        widgets["unique_only"] = unique_var

        # LIGNE 1 : Cible + Combobox + Checkbox
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=2)

        ttk.Label(line1, text="Cible : ").pack(side="left", padx=5)
        ttk.Combobox(line1, textvariable=mode_var, values=DOWNLOAD_MODES, state="readonly", width=7).pack(
            side="left", fill="x", expand=False, padx=(5, 25)
        )
        CanvasCheckbox(line1, text="Doublons interdits", variable=unique_var).pack(side="left", padx=5)

        # LIGNE 2 : Hauteur (px) + Min + Spinbox + Max + Spinbox
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=2)

        ttk.Label(line2, text="Hauteur (px) : ", width=10).pack(side="left", padx=5)
        ttk.Label(line2, text="Min.").pack(side="left", padx=2)
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=8).pack(
            side="left", padx=5
        )
        ttk.Label(line2, text="Max.").pack(side="left", padx=2)
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=8).pack(
            side="left", padx=5
        )
        widgets["height_min"] = height_min_var
        widgets["height_max"] = height_max_var

        # LIGNE 3 : Largeur (px) + Min + Spinbox + Max + Spinbox
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=2)

        ttk.Label(line3, text="Largeur (px) : ", width=10).pack(side="left", padx=5)
        ttk.Label(line3, text="Min.").pack(side="left", padx=2)
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=8).pack(
            side="left", padx=5
        )
        ttk.Label(line3, text="Max.").pack(side="left", padx=2)
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=8).pack(
            side="left", padx=5
        )
        widgets["width_min"] = width_min_var
        widgets["width_max"] = width_max_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["mode"].set(params.get("mode", "largest"))
        widgets["unique_only"].set(bool(params.get("unique_only", False)))
        widgets["height_min"].set(str(params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["height_max"].set(str(params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["width_min"].set(str(params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["width_max"].set(str(params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": widgets["mode"].get(),
            "unique_only": bool(widgets["unique_only"].get()),
            "height_min": safe_int_widget(widgets, "height_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "height_max": safe_int_widget(widgets, "height_max", C_MAXIMUM_SIZE_IMAGE),
            "width_min": safe_int_widget(widgets, "width_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
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
        width_min = params.get("width_min", 200)
        height_min = params.get("height_min", 200)
        width_max = params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
        height_max = params.get("height_max", C_MAXIMUM_SIZE_IMAGE)
        dup_str = "(doublons refusés)" if unique_only else "(doublons autorisés)"
        return f"Télécharger images {dup_str}\n{mode} - {width_min}x{height_min} -> {width_max}x{height_max}"


register_form(DownloadImageFormDef())
