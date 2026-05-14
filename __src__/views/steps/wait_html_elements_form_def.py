"""IStepFormDef for WAIT_HTML_ELEMENTS."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import (
    C_MAXIMUM_QTY_COUNTER,
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"
C_INPUT_DEFAULT_RETRY_UNIT = C_UNITS_TIME_ALLOWED_FOR_VIEW[-1]  # ms
C_INPUT_DEFAULT_RETRY_DELAY = 400

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WaitHtmlElementsFormDef(IStepFormDef):
    """Form definition for waiting until an element is present."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the StepType handled by this form."""
        return StepTypeEnum.E_WAIT_HTML_ELEMENTS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_WAIT_HTML_ELEMENTS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the selector and timeout widgets into the given frame."""
        # ROW 1 — selector
        self._build_subform_selector(frame, widgets)

        # ROW 2 — waiting elements
        self._build_subform_waiting_elements(frame, widgets)

        # ROW 3 — retry every
        self._build_subform_retry_delay(frame, widgets)

        # ROW 4 — comment
        self._build_subform_comment(frame, widgets)

    def _build_subform_selector(self, frame, widgets):
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        ttk.Label(line1, text="Sélecteur CSS :").pack(side=tk.LEFT, padx=(0, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(line1, textvariable=sel_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        widgets["selector"] = sel_var

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
        """Load stored parameters into the form widgets."""
        widgets["selector"].set(model.params.get("selector", C_INPUT_DEFAULT_CSS_SELECTOR))
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
        """Read widget values into a parameters mapping."""
        op_display = widgets["operator"].get()
        op_value = COUNT_OP_VIEW_TO_MODEL.get(op_display, "equal")

        return {
            "selector": widgets["selector"].get().strip(),
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
        selector = model.params.get("selector")

        retry_delay = model.params.get("retry_delay", C_INPUT_DEFAULT_RETRY_DELAY)
        retry_unit = model.params.get("retry_unit", C_UNITS_TIME_DEFAULT_MODEL)
        unit_display = WAIT_UNIT_MODEL_TO_VIEW.get(retry_unit, retry_unit)

        return f"Attendre éléments  -  Toutes les : {retry_delay} {unit_display}\n" + f"Sél. : {selector}"


register_form(WaitHtmlElementsFormDef())
