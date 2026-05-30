"""IStepFormDef for SCROLL_DOWN."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, cast, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from models.steps.scroll_down_params import ScrollDownParams
from models.steps_context_model import StepsContext
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_PIXELS_DISTANCE = "pixels"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


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
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_pixels(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_pixels(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the scroll distance spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_PIXELS_DISTANCE tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Pixels:").pack(side="left", padx=(0, 5))
        pixels_var = tk.StringVar(value="1000")
        ttk.Spinbox(row0, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=pixels_var, width=10).pack(
            side="left", padx=(0, 5),
        )
        widgets[C_KEY_PIXELS_DISTANCE] = pixels_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Commentaire :").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        p = cast(ScrollDownParams, model.params)
        widgets[C_KEY_PIXELS_DISTANCE].set(str(p.pixels))
        widgets[C_KEY_COMMENT].set(p.comment)

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        return {
            C_KEY_PIXELS_DISTANCE: safe_int_widget(widgets, C_KEY_PIXELS_DISTANCE, -1),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int, steps_context: StepsContext) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        p = cast(ScrollDownParams, model.params)
        return f"Défilement vers le bas\nLongueur: {p.pixels} px"


register_form(ScrollDownFormDef())


# EOF
