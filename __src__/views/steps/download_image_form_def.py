"""IStepFormDef for DOWNLOAD_IMAGE."""

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
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox
from views.steps._constants import DOWNLOAD_MODES, safe_int_from_dict

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_MINIMUM_SIZE = 250
C_INPUT_DEFAULT_MODE_DDL = DOWNLOAD_MODES[-1]  # all

C_KEY_MODE = "mode"
C_KEY_UNIQUE_ONLY = "unique_only"
C_KEY_HEIGHT_MIN = "height_min"
C_KEY_HEIGHT_MAX = "height_max"
C_KEY_WIDTH_MIN = "width_min"
C_KEY_WIDTH_MAX = "width_max"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DownloadImageFormDef(IStepFormDef):
    """Form definition for the download image scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_DOWNLOAD_IMAGE

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_DOWNLOAD_IMAGE)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_mode(frame, widgets)
        self._build_subform_height(frame, widgets)
        self._build_subform_width(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_mode(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the download mode combobox and duplicate-filter checkbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_MODE and C_KEY_UNIQUE_ONLY tk.Variables.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        mode_var = tk.StringVar(value=C_INPUT_DEFAULT_MODE_DDL)
        unique_var = tk.BooleanVar(value=True)
        widgets[C_KEY_MODE] = mode_var
        widgets[C_KEY_UNIQUE_ONLY] = unique_var

        ttk.Label(line1, text="Cible :").pack(side="left", padx=(0, 5))
        ttk.Combobox(line1, textvariable=mode_var, values=DOWNLOAD_MODES, state="readonly", width=7).pack(
            side="left", fill="x", expand=False, padx=(0, 25)
        )
        CanvasCheckbox(line1, text="Doublons interdits", variable=unique_var).pack(side="left", padx=(10, 4))

    @staticmethod
    def _build_subform_height(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the height min/max spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_HEIGHT_MIN and C_KEY_HEIGHT_MAX tk.Variables.
        """
        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        ttk.Label(line2, text="Hauteur entre :", width=15).pack(side="left", padx=(0, 5))
        height_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_min_var, width=8).pack(
            side="left", padx=(0, 5)
        )
        ttk.Label(line2, text=" et ").pack(side="left", padx=(0, 5))
        height_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line2, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=height_max_var, width=8).pack(
            side="left", padx=(0, 5)
        )
        widgets[C_KEY_HEIGHT_MIN] = height_min_var
        widgets[C_KEY_HEIGHT_MAX] = height_max_var

    @staticmethod
    def _build_subform_width(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the width min/max spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_WIDTH_MIN and C_KEY_WIDTH_MAX tk.Variables.
        """
        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Largeur entre :", width=15).pack(side="left", padx=(0, 5))
        width_min_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MINIMUM_SIZE))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_min_var, width=8).pack(
            side="left", padx=(0, 5)
        )
        ttk.Label(line3, text=" et ").pack(side="left", padx=(0, 5))
        width_max_var = tk.StringVar(value=str(C_MAXIMUM_SIZE_IMAGE))
        ttk.Spinbox(line3, from_=0, to=C_MAXIMUM_SIZE_IMAGE, textvariable=width_max_var, width=8).pack(
            side="left", padx=(0, 5)
        )
        widgets[C_KEY_WIDTH_MIN] = width_min_var
        widgets[C_KEY_WIDTH_MAX] = width_max_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        line4 = ttk.Frame(frame)
        line4.pack(fill="x", pady=(0, 8))

        ttk.Label(line4, text="Commentaire :").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line4, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_MODE].set(params_dict.get(C_KEY_MODE, C_INPUT_DEFAULT_MODE_DDL))
        widgets[C_KEY_UNIQUE_ONLY].set(bool(params_dict.get(C_KEY_UNIQUE_ONLY, True)))
        widgets[C_KEY_HEIGHT_MIN].set(str(params_dict.get(C_KEY_HEIGHT_MIN, C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets[C_KEY_HEIGHT_MAX].set(str(params_dict.get(C_KEY_HEIGHT_MAX, C_MAXIMUM_SIZE_IMAGE)))
        widgets[C_KEY_WIDTH_MIN].set(str(params_dict.get(C_KEY_WIDTH_MIN, C_INPUT_DEFAULT_MINIMUM_SIZE)))
        widgets[C_KEY_WIDTH_MAX].set(str(params_dict.get(C_KEY_WIDTH_MAX, C_MAXIMUM_SIZE_IMAGE)))
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
            C_KEY_MODE: widgets[C_KEY_MODE].get(),
            C_KEY_UNIQUE_ONLY: bool(widgets[C_KEY_UNIQUE_ONLY].get()),
            C_KEY_HEIGHT_MIN: safe_int_from_dict(widgets, C_KEY_HEIGHT_MIN, -1),
            C_KEY_HEIGHT_MAX: safe_int_from_dict(widgets, C_KEY_HEIGHT_MAX, -1),
            C_KEY_WIDTH_MIN: safe_int_from_dict(widgets, C_KEY_WIDTH_MIN, -1),
            C_KEY_WIDTH_MAX: safe_int_from_dict(widgets, C_KEY_WIDTH_MAX, -1),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(DownloadImageFormDef())


# EOF
