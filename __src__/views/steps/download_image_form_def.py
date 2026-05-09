"""IStepFormDef for DOWNLOAD_IMAGE."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import DOWNLOAD_MODES, safe_int_widget

from __src__.shared.i18n_fra import C_STEP_TYPE_TO_LABELS

C_INPUT_DEFAULT_MINIMUM_SIZE = 250
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
        """Return the step type."""
        return StepType.DOWNLOAD_IMAGE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepType.DOWNLOAD_IMAGE)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
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

        ttk.Label(line2, text="Hauteur entre : ", width=15).pack(side="left", padx=5)
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=8).pack(
            side="left", padx=5
        )
        ttk.Label(line2, text=" et ").pack(side="left", padx=2)
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=8).pack(
            side="left", padx=5
        )
        widgets["height_min"] = height_min_var
        widgets["height_max"] = height_max_var

        # LIGNE 3 : Largeur (px) + Min + Spinbox + Max + Spinbox
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=2)

        ttk.Label(line3, text="Largeur entre : ", width=15).pack(side="left", padx=5)
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=8).pack(
            side="left", padx=5
        )
        ttk.Label(line3, text=" et ").pack(side="left", padx=2)
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=8).pack(
            side="left", padx=5
        )
        widgets["width_min"] = width_min_var
        widgets["width_max"] = width_max_var

    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["mode"].set(model.params.get("mode", "largest"))
        widgets["unique_only"].set(bool(model.params.get("unique_only", False)))
        widgets["height_min"].set(str(model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["height_max"].set(str(model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["width_min"].set(str(model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["width_max"].set(str(model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "mode": widgets["mode"].get(),
            "unique_only": bool(widgets["unique_only"].get()),
            "height_min": safe_int_widget(widgets, "height_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "height_max": safe_int_widget(widgets, "height_max", C_MAXIMUM_SIZE_IMAGE),
            "width_min": safe_int_widget(widgets, "width_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "width_max": safe_int_widget(widgets, "width_max", C_MAXIMUM_SIZE_IMAGE),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []

        v_height_min = safe_int_widget(widgets, "height_min", -1)
        v_height_max = safe_int_widget(widgets, "height_max", -1)
        v_width_min = safe_int_widget(widgets, "width_min", -1)
        v_width_max = safe_int_widget(widgets, "width_max", -1)

        # Validate non-negativity.
        if v_height_min < 0:
            errors.append("Hauteur min. doit être >= 0.")
        if v_height_max < 1:
            errors.append("Hauteur max. doit être >= 1.")
        if v_width_min < 0:
            errors.append("Largeur min. doit être >= 0.")
        if v_width_max < 1:
            errors.append("Largeur max. doit être >= 1.")

        # Validate min <= max constraints.
        if v_height_min > v_height_max:
            errors.append("Hauteur min. doit être <= hauteur max.")
        if v_width_min > v_width_max:
            errors.append("Largeur min. doit être <= largeur max.")

        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        mode = model.params.get("mode", "")
        unique_only = model.params.get("unique_only", False)
        width_min = model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        height_min = model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        width_max = model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
        height_max = model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)
        dup_str = "(doublons refusés)" if unique_only else "(doublons autorisés)"
        return f"Télécharger images {dup_str}\n{mode} - {width_min}x{height_min} -> {width_max}x{height_max}"


register_form(DownloadImageFormDef())
