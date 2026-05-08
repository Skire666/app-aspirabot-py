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

from __src__.shared.i18n_fra import C_STEP_TYPE_TO_LABELS

C_INPUT_DEFAULT_MINIMUM_SIZE = 250
C_INPUT_DEFAULT_TIMEOUT_DURATION = 8
C_INPUT_DEFAULT_TIMEOUT_UNIT = C_UNITS_TIME_DEFAULT_VIEW


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
        return C_STEP_TYPE_TO_LABELS.get(StepType.WAIT_IMAGE_SIZE)

    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        # LIGNE 1 : Hauteur (px) + Min + Spinbox + Max + Spinbox
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=2)

        ttk.Label(line1, text="Hauteur entre : ", width=10).pack(side="left")
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=8).pack(
            side="left", padx=5
        )
        ttk.Label(line1, text="et").pack(side="left", padx=2)
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=8).pack(
            side="left", padx=5
        )
        widgets["height_min"] = height_min_var
        widgets["height_max"] = height_max_var

        # LIGNE 2 : Largeur (px) + Min + Spinbox + Max + Spinbox
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=2)

        ttk.Label(line2, text="Largeur entre : ", width=10).pack(side="left")
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=8).pack(
            side="left", padx=5
        )
        ttk.Label(line2, text="et").pack(side="left", padx=2)
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=8).pack(
            side="left", padx=5
        )
        widgets["width_min"] = width_min_var
        widgets["width_max"] = width_max_var

        ## dernière ligne
        td_var = tk.StringVar(value=str(C_INPUT_DEFAULT_TIMEOUT_DURATION))
        tu_var = tk.StringVar(value=C_UNITS_TIME_DEFAULT_VIEW)
        widgets["timeout_duration"] = td_var
        widgets["timeout_unit"] = tu_var

        timeout_frame = ttk.Frame(frame)
        timeout_frame.pack(fill="x", pady=2)
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
