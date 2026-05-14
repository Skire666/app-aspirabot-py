"""IStepFormDef for SCROLL_DOWN."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ScrollDownFormDef(IStepFormDef):
    """Form definition for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_SCROLL_DOWN)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the form widgets into the given frame."""
        # ROW 0
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Pixels:").pack(side="left", padx=(0, 5))
        pixels_var = tk.StringVar(value="1000")
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=pixels_var, width=10).pack(
            side="left", padx=(0, 5)
        )
        widgets["pixels"] = pixels_var

        # ROW 1 — comment
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))
        ttk.Label(row1, text="Commentaire :").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets["comment"] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters into form widgets."""
        widgets["pixels"].set(str(model.params.get("pixels", 1000)))
        widgets["comment"].set(model.params.get("comment", ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a parameters dict."""
        return {
            "pixels": safe_int_widget(widgets, "pixels", -1),
            "comment": widgets["comment"].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance."""
        return f"Défilement vers le bas\nLongueur: {model.params.get('pixels', 0)} px"


register_form(ScrollDownFormDef())
