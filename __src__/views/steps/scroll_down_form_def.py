"""IStepFormDef for SCROLL_DOWN."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.enums import StepTypeEnum
from shared.parse_util import safe_int_from_dict
from shared.step_registry import register_form

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_PIXELS_DISTANCE = "pixels"
C_KEY_NBR_LOOPS = "nbr_loops"
C_KEY_DELAY_PAUSE = "delay_pause"
C_KEY_COMMENT = "comment"

C_LIMIT_GIVE_UP_SCROLLING = 4  # number of consecutive no-growth iterations before giving up on scrolling --- IGNORE ---

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScrollDownFormDef(IStepFormDef):
    """Form definition for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_pixels(frame, widgets)
        self._build_subform_nbr_loops(frame, widgets)
        self._build_subform_delay_pause(frame, widgets)
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
            side="left", padx=(0, 5)
        )
        widgets[C_KEY_PIXELS_DISTANCE] = pixels_var

    @staticmethod
    def _build_subform_nbr_loops(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Nombre de boucle :").pack(side="left", padx=(0, 5))
        nbr_loops_var = tk.StringVar(value="1")
        ttk.Entry(row1, textvariable=nbr_loops_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(row1, text=f"(abandonne si stable depuis {C_LIMIT_GIVE_UP_SCROLLING} tours)").pack(
            side="left", padx=(0, 5)
        )
        widgets[C_KEY_NBR_LOOPS] = nbr_loops_var

    @staticmethod
    def _build_subform_delay_pause(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Pause entre chaque (sec.) :").pack(side="left", padx=(0, 5))
        delay_pause_var = tk.StringVar(value="1")
        ttk.Entry(row2, textvariable=delay_pause_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(row2, text="(ignoré lors de la 1ère boucle)").pack(side="left", padx=(0, 5))
        widgets[C_KEY_DELAY_PAUSE] = delay_pause_var

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
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_PIXELS_DISTANCE].set(str(params_dict.get(C_KEY_PIXELS_DISTANCE, 1000)))
        widgets[C_KEY_NBR_LOOPS].set(str(params_dict.get(C_KEY_NBR_LOOPS, 1)))
        widgets[C_KEY_DELAY_PAUSE].set(str(params_dict.get(C_KEY_DELAY_PAUSE, 0)))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        return {
            C_KEY_PIXELS_DISTANCE: safe_int_from_dict(widgets, C_KEY_PIXELS_DISTANCE, -1),
            C_KEY_NBR_LOOPS: safe_int_from_dict(widgets, C_KEY_NBR_LOOPS, 1),
            C_KEY_DELAY_PAUSE: safe_int_from_dict(widgets, C_KEY_DELAY_PAUSE, 0),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(ScrollDownFormDef())


# EOF
