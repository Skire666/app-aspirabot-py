"""IStepFormDef for WAIT_HTML_IMAGES."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import (
    C_MAXIMUM_QTY_COUNTER,
    C_MAXIMUM_SIZE_IMAGE,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_MODEL,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    COUNT_OP_DISPLAY,
    COUNT_OP_VIEW_TO_MODEL,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)
from views.steps.wait_html_elements_form_def import C_INPUT_DEFAULT_RETRY_DELAY

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_MINIMUM_SIZE = 250
C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_RETRY_UNIT = C_UNITS_TIME_ALLOWED_FOR_VIEW[-1]  # ms

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WaitHtmlImagesFormDef(IStepFormDef):
    """Form definition for waiting until an image of a given size appears.

    Provides widget construction, parameter (de)serialization and validation.
    """

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepType handled by this form definition."""
        return StepTypeEnum.E_WAIT_HTML_IMAGES

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_HTML_IMAGES)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # LIGNE 1 : Hauteur (px) + Min + Spinbox + Max + Spinbox
        self._build_subform_width_height(frame, widgets)

        # ROW 2 — waiting elements
        self._build_subform_waiting_elements(frame, widgets)

        # ROW 3 — retry every
        self._build_subform_retry_delay(frame, widgets)

        # ROW 4 — comment
        self._build_subform_comment(frame, widgets)

    def _build_subform_width_height(self, frame, widgets):
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Largeur entre").pack(side="left", padx=(0, 5))
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=5).pack(side="left")
        ttk.Label(line1, text=" et ").pack(side="left")
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=6).pack(side="left")
        widgets["width_min"] = width_min_var
        widgets["width_max"] = width_max_var

        ttk.Label(line1, text="Hauteur entre").pack(side="left", padx=(24, 5))
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=5).pack(
            side="left"
        )
        ttk.Label(line1, text=" et ").pack(side="left")
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=6).pack(
            side="left"
        )
        widgets["height_min"] = height_min_var
        widgets["height_max"] = height_max_var

    def _build_subform_waiting_elements(self, frame, widgets):
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Attendre un nombre").pack(side=tk.LEFT, padx=(0, 5))

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[-1])  # supérieur ou égal
        op_cb = ttk.Combobox(row2, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18)
        op_cb.pack(side=tk.LEFT, padx=(0, 5))
        widgets["operator"] = op_var

        val_var = tk.StringVar(value="1")
        ttk.Spinbox(row2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=val_var, width=6).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets["quantity"] = val_var
        ttk.Label(row2, text="d'élément(s)").pack(side=tk.LEFT, padx=(0, 5))

    def _build_subform_retry_delay(self, frame, widgets):
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Toutes les").pack(side=tk.LEFT, padx=(0, 5))
        every_var = tk.StringVar(value=str(C_INPUT_DEFAULT_RETRY_DELAY))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=every_var, width=7).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        unit_var = tk.StringVar(value=C_INPUT_DEFAULT_RETRY_UNIT)
        ttk.Combobox(
            line2, textvariable=unit_var, values=C_UNITS_TIME_ALLOWED_FOR_VIEW, state="readonly", width=10
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(line2, text="avec").pack(side=tk.LEFT, padx=(0, 5))
        max_var = tk.StringVar(value="10")
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=max_var, width=6).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Label(line2, text="essai(s) max.").pack(side=tk.LEFT)

        widgets["retry_delay"] = every_var
        widgets["retry_unit"] = unit_var
        widgets["retry_max"] = max_var

    def _build_subform_comment(self, frame, widgets):
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Populate widget values from stored parameters.

        Args:
            model: Step model containing stored parameters.
            widgets: Mapping of form widgets to populate.
        """
        widgets["height_min"].set(str(model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["height_max"].set(str(model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["width_min"].set(str(model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets["width_max"].set(str(model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)))
        widgets["operator"].set(model.params.get("operator", COUNT_OP_DISPLAY[-1]))
        widgets["quantity"].set(str(model.params.get("quantity", 1)))
        widgets["retry_delay"].set(str(model.params.get("retry_delay", C_INPUT_DEFAULT_RETRY_DELAY)))
        widgets["retry_unit"].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(
                model.params.get("retry_unit", C_UNITS_TIME_DEFAULT_MODEL), C_UNITS_TIME_DEFAULT_VIEW
            )
        )
        widgets["retry_max"].set(str(model.params.get("retry_max", 10)))
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        op_display = widgets["operator"].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")

        return {
            "height_min": safe_int_widget(widgets, "height_min", -1),
            "height_max": safe_int_widget(widgets, "height_max", -1),
            "width_min": safe_int_widget(widgets, "width_min", -1),
            "width_max": safe_int_widget(widgets, "width_max", -1),
            "operator": op_value,
            "quantity": safe_int_widget(widgets, "quantity", -1),
            "retry_delay": safe_int_widget(widgets, "retry_delay", -1),
            "retry_unit": WAIT_UNIT_VIEW_TO_MODEL.get(widgets["retry_unit"].get()),
            "retry_max": safe_int_widget(widgets, "retry_max", -1),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact label for the workflow list."""
        retry_delay = model.params.get("retry_delay", C_INPUT_DEFAULT_RETRY_DELAY)
        retry_unit = model.params.get("retry_unit", C_UNITS_TIME_DEFAULT_MODEL)
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(retry_unit, retry_unit)

        width_min = model.params.get("width_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        height_min = model.params.get("height_min", C_INPUT_DEFAULT_MINIMUM_SIZE)
        width_max = model.params.get("width_max", C_MAXIMUM_SIZE_IMAGE)
        height_max = model.params.get("height_max", C_MAXIMUM_SIZE_IMAGE)

        return f"Attendre images  -  Toutes les : {retry_delay} {unit_display}\n Taille : {width_min}x{height_min} -> {width_max}x{height_max}"


register_form(WaitHtmlImagesFormDef())
