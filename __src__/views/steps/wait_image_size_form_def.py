"""IStepFormDef for WAIT_IMAGE_SIZE."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_UNITS_TIME_ALLOWED_FOR_VIEW, C_UNITS_TIME_DEFAULT_MODEL, C_UNITS_TIME_DEFAULT_VIEW
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget


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


class WaitImageSizeFormDef(IStepFormDef):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.WAIT_IMAGE_SIZE

    @classmethod
    def label(cls) -> str:
        return "Vérifier une taille d'image"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        frame.columnconfigure(2, weight=1)
        _add_dimension_row(frame, widgets, 0, "Hauteur (px):", "height_min", "height_max", 0, C_MAXIMUM_SIZE_IMAGE)
        _add_dimension_row(frame, widgets, 1, "Largeur (px):", "width_min", "width_max", 0, C_MAXIMUM_SIZE_IMAGE)

        timeout_frame = ttk.Frame(frame)
        timeout_frame.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=4)
        ttk.Label(timeout_frame, text="Timeout").pack(side=tk.LEFT, padx=(0, 4))
        td_var = tk.StringVar(value="0")
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        tu_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        ttk.Combobox(timeout_frame, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(timeout_frame, text="(0 = désactivé)", foreground="gray").pack(side=tk.LEFT)
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        widgets["height_min"].set(str(params.get("height_min", 0)))
        widgets["height_max"].set(str(params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["width_min"].set(str(params.get("width_min", 0)))
        widgets["width_max"].set(str(params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["timeout_duration"].set(str(params.get("timeout_duration", 0)))
        widgets["timeout_unit"].set(WAIT_UNIT_MODEL_TO_VIEW.get(params.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW))

    def read_params(self, widgets: dict[str, Any]) -> dict[str, Any]:
        return {
            "height_min": safe_int_widget(widgets, "height_min", 0),
            "height_max": safe_int_widget(widgets, "height_max", C_MAXIMUM_SIZE_IMAGE),
            "width_min": safe_int_widget(widgets, "width_min", 0),
            "width_max": safe_int_widget(widgets, "width_max", C_MAXIMUM_SIZE_IMAGE),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", 0),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if safe_int_widget(widgets, key, -1) < 0:
                errors.append(f"La valeur '{key}' doit être un entier positif ou égal à 0.")
        if safe_int_widget(widgets, "timeout_duration", -1) < 0:
            errors.append("Durée de timeout doit être un nombre positif.")
        return errors

    def format_label(self, params: dict[str, Any], idx: int) -> str:
        width_min = params.get("width_min", 0)
        height_min = params.get("height_min", 0)
        width_max = params.get("width_max", 0)
        height_max = params.get("height_max", 0)
        label = f"Vérifier une taille d'image\n{width_min}x{height_min} -> {width_max}x{height_max}"
        td = params.get("timeout_duration", 0)
        if td:
            label += f" [timeout: {td} {params.get('timeout_unit', '')}]"
        return label


register_form(WaitImageSizeFormDef())
