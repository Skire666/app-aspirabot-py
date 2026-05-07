"""IStepFormDef for WAIT_IMAGE_SIZE."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel, StepType
from shared.constants import (
    C_MAXIMUM_SIZE_IMAGE,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.step_registry import register_form
from views.steps._constants import WAIT_UNIT_MODEL_TO_VIEW, WAIT_UNIT_VIEW_TO_MODEL, safe_int_widget

C_INPUT_DEFAULT_MINIMUM_SIZE = 200
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW


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
    min_var = tk.StringVar(value=str(default_min))
    max_var = tk.StringVar(value=str(default_max))
    widgets[min_key] = min_var
    widgets[max_key] = max_var

    row_frame = ttk.Frame(frame)
    row_frame.grid(row=row, column=0, columnspan=5, sticky="w", padx=5, pady=4)

    ttk.Label(row_frame, text=label, width=15).pack(side=tk.LEFT, padx=(0, 6))
    ttk.Label(row_frame, text=" Min : ").pack(side=tk.LEFT, padx=(0, 8))
    ttk.Spinbox(row_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=min_var, width=8).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    ttk.Label(row_frame, text=" Max : ").pack(side=tk.LEFT)
    ttk.Spinbox(row_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=max_var, width=8).pack(
        side=tk.LEFT, padx=(0, 4)
    )


class WaitImageSizeFormDef(IStepFormDef):
    """Form definition for waiting until an image of a given size appears.

    Provides widget construction, parameter (de)serialization and validation.
    """

    @classmethod
    def step_type(cls) -> StepType:
        """Return the StepType handled by this form definition."""
        return StepType.WAIT_IMAGE_SIZE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return "Présence taille d'image"

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Create the form widgets and arrange them in `frame`.

        The layout uses a fixed set of columns so rows align left-to-right.
        """
        # Ensure columns are configured so widgets align left-to-right
        for c in range(5):
            frame.columnconfigure(c, weight=0)
        # allow the main middle column to expand if there is extra space
        frame.columnconfigure(1, weight=1)
        _add_dimension_row(
            frame,
            widgets,
            0,
            "Hauteur (px) : ",
            "height_min",
            "height_max",
            C_INPUT_DEFAULT_MINIMUM_SIZE,
            C_MAXIMUM_SIZE_IMAGE,
        )
        _add_dimension_row(
            frame,
            widgets,
            1,
            "Largeur (px) : ",
            "width_min",
            "width_max",
            C_INPUT_DEFAULT_MINIMUM_SIZE,
            C_MAXIMUM_SIZE_IMAGE,
        )

        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        tu_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

        timeout_frame = ttk.Frame(frame)
        timeout_frame.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=4)
        ttk.Label(timeout_frame, text="Timeout : ").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Spinbox(timeout_frame, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=td_var, width=7).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Combobox(
            timeout_frame, textvariable=tu_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 4))

    def load_params(self, params: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Populate widget values from stored parameters.

        Args:
            params: Mapping of step parameters.
            widgets: Mapping of form widgets to populate.
        """
        widgets["height_min"].set(str(params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["height_max"].set(str(params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["width_min"].set(str(params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["width_max"].set(str(params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["timeout_duration"].set(str(params.get("timeout_duration", C_INPUT_DEFAULT_TIMEOUT_DURATION)))
        widgets["timeout_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                params.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )

    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "height_min": safe_int_widget(widgets, "height_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "height_max": safe_int_widget(widgets, "height_max", C_MAXIMUM_SIZE_IMAGE),
            "width_min": safe_int_widget(widgets, "width_min", C_INPUT_DEFAULT_MINIMUM_SIZE),
            "width_max": safe_int_widget(widgets, "width_max", C_MAXIMUM_SIZE_IMAGE),
            "timeout_duration": safe_int_widget(widgets, "timeout_duration", C_INPUT_DEFAULT_TIMEOUT_DURATION),
            "timeout_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["timeout_unit"].get(), C_UNITS_TIME_DEFAULT_MODEL),
        }

    def validate_form(self, widgets: dict[str, Any]) -> list[str]:
        """Validate current widget values and return a list of error messages."""
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if safe_int_widget(widgets, key, -1) < 0:
                errors.append(f"La valeur '{key}' doit être un entier positif ou égal à 0.")
        if safe_int_widget(widgets, "timeout_duration", -1) < 1:
            errors.append("Durée de timeout doit être un nombre supérieur ou égal à 1.")
        return errors

    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Produce a compact, human-readable label describing this step instance."""
        width_min = model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        height_min = model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        width_max = model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
        height_max = model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)

        unit_time = model.params.get("timeout_unit", "")
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(unit_time, unit_time)
        td = model.params.get("timeout_duration", 0)

        label = f"Présence d'une image  -  timeout : {td} {unit_display}\n"
        return label + f"{width_min}x{height_min} -> {width_max}x{height_max}"


register_form(WaitImageSizeFormDef())
