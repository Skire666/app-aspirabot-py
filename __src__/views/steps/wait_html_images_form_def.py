"""IStepFormDef for WAIT_HTML_IMAGES."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, cast, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from models.steps_context_model import StepsContext
from shared.constants import (
    C_MAXIMUM_QTY_COUNTER,
    C_MAXIMUM_SIZE_IMAGE,
    C_UNITS_TIME_ALLOWED_FOR_VIEW,
    C_UNITS_TIME_DEFAULT_VIEW,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    COUNT_OP_DISPLAY,
    COUNT_OP_MODEL_TO_VIEW,
    COUNT_OP_VIEW_TO_MODEL,
    WAIT_UNIT_MODEL_TO_VIEW,
    WAIT_UNIT_VIEW_TO_MODEL,
    safe_int_widget,
)
from views.steps.wait_html_elements_form_def import C_INPUT_DEFAULT_RETRY_DELAY

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_MINIMUM_SIZE = 250
C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_RETRY_UNIT = C_UNITS_TIME_ALLOWED_FOR_VIEW[-1]  # ms

C_KEY_WIDTH_MIN = "width_min"
C_KEY_WIDTH_MAX = "width_max"
C_KEY_HEIGHT_MIN = "height_min"
C_KEY_HEIGHT_MAX = "height_max"
C_KEY_OPERATOR = "operator"
C_KEY_QUANTITY_EXPECTED = "quantity"
C_KEY_RETRY_DELAY = "retry_delay"
C_KEY_RETRY_UNIT = "retry_unit"
C_KEY_RETRY_MAX = "retry_max"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WaitHtmlImagesFormDef(IStepFormDef):
    """Form definition for waiting until an image of a given size appears.

    Provides widget construction, parameter (de)serialization and validation.
    """

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepTypeEnum handled by this form definition."""
        return StepTypeEnum.E_WAIT_HTML_IMAGES

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_HTML_IMAGES)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_width_height(frame, widgets)
        self._build_subform_waiting_elements(frame, widgets)
        self._build_subform_retry_delay(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_width_height(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the width and height min/max spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_WIDTH_MIN, C_KEY_WIDTH_MAX,
                C_KEY_HEIGHT_MIN, and C_KEY_HEIGHT_MAX tk.Variables.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Largeur entre").pack(side="left", padx=(0, 5))
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=5).pack(side="left")
        ttk.Label(line1, text=" et ").pack(side="left")
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=6).pack(side="left")
        widgets[C_KEY_WIDTH_MIN] = width_min_var
        widgets[C_KEY_WIDTH_MAX] = width_max_var

        ttk.Label(line1, text="Hauteur entre").pack(side="left", padx=(30, 5))
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=5).pack(side="left")
        ttk.Label(line1, text=" et ").pack(side="left")
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line1, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=6).pack(side="left")
        widgets[C_KEY_HEIGHT_MIN] = height_min_var
        widgets[C_KEY_HEIGHT_MAX] = height_max_var

    @staticmethod
    def _build_subform_waiting_elements(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the image count operator and quantity spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_OPERATOR and C_KEY_QUANTITY_EXPECTED tk.Variables.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Attendre un nombre").pack(side=tk.LEFT, padx=(0, 5))

        op_var = tk.StringVar(value=COUNT_OP_DISPLAY[-1])
        ttk.Combobox(row2, textvariable=op_var, values=COUNT_OP_DISPLAY, state="readonly", width=18).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_OPERATOR] = op_var

        val_var = tk.StringVar(value="1")
        ttk.Spinbox(row2, from_=0, to=C_MAXIMUM_QTY_COUNTER, textvariable=val_var, width=6).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        widgets[C_KEY_QUANTITY_EXPECTED] = val_var
        ttk.Label(row2, text="d'élément(s)").pack(side=tk.LEFT, padx=(0, 5))

    @staticmethod
    def _build_subform_retry_delay(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the retry interval spinbox, time unit combobox, and max attempts spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_RETRY_DELAY, C_KEY_RETRY_UNIT,
                and C_KEY_RETRY_MAX tk.Variables.
        """
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

        widgets[C_KEY_RETRY_DELAY] = every_var
        widgets[C_KEY_RETRY_UNIT] = unit_var
        widgets[C_KEY_RETRY_MAX] = max_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        p = cast(WaitHtmlImagesParams, model.params)
        widgets[C_KEY_HEIGHT_MIN].set(str(p.height_min))
        widgets[C_KEY_HEIGHT_MAX].set(str(p.height_max))
        widgets[C_KEY_WIDTH_MIN].set(str(p.width_min))
        widgets[C_KEY_WIDTH_MAX].set(str(p.width_max))

        op_display = COUNT_OP_MODEL_TO_VIEW.get(p.operator, COUNT_OP_DISPLAY[-1])
        widgets[C_KEY_OPERATOR].set(op_display)
        widgets[C_KEY_QUANTITY_EXPECTED].set(str(p.quantity))
        widgets[C_KEY_RETRY_DELAY].set(str(p.retry_delay))
        widgets[C_KEY_RETRY_UNIT].set(
            WAIT_UNIT_MODEL_TO_VIEW.get(p.retry_unit, C_UNITS_TIME_DEFAULT_VIEW)
        )
        widgets[C_KEY_RETRY_MAX].set(str(p.retry_max))
        widgets[C_KEY_COMMENT].set(p.comment)

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        op_display = widgets[C_KEY_OPERATOR].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")

        return {
            C_KEY_HEIGHT_MIN: safe_int_widget(widgets, C_KEY_HEIGHT_MIN, -1),
            C_KEY_HEIGHT_MAX: safe_int_widget(widgets, C_KEY_HEIGHT_MAX, -1),
            C_KEY_WIDTH_MIN: safe_int_widget(widgets, C_KEY_WIDTH_MIN, -1),
            C_KEY_WIDTH_MAX: safe_int_widget(widgets, C_KEY_WIDTH_MAX, -1),
            C_KEY_OPERATOR: op_value,
            C_KEY_QUANTITY_EXPECTED: safe_int_widget(widgets, C_KEY_QUANTITY_EXPECTED, -1),
            C_KEY_RETRY_DELAY: safe_int_widget(widgets, C_KEY_RETRY_DELAY, -1),
            C_KEY_RETRY_UNIT: WAIT_UNIT_VIEW_TO_MODEL.get(widgets[C_KEY_RETRY_UNIT].get()),
            C_KEY_RETRY_MAX: safe_int_widget(widgets, C_KEY_RETRY_MAX, -1),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int, steps_context: StepsContext) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.
            steps_context: Step execution context.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        p = cast(WaitHtmlImagesParams, model.params)
        retry_delay = p.retry_delay
        retry_unit = p.retry_unit
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(retry_unit, retry_unit)

        width_min = p.width_min
        height_min = p.height_min
        width_max = p.width_max
        height_max = p.height_max

        return (
            f"Attendre images  -  Toutes les : {retry_delay} {unit_display}\n"
            f"Taille : {width_min}x{height_min} -> {width_max}x{height_max}"
        )


register_form(WaitHtmlImagesFormDef())


# EOF
