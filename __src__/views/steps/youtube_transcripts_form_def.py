"""IStepFormDef for YOUTUBE_DDL."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from shared.enums import StepTypeEnum
from shared.step_registry import register_form
from views.components.canvas_checkbox import CanvasCheckbox

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_KEY_TITLE = "title"
C_KEY_COMMENT = "comment"
C_KEY_BASIC_INFO = "basic_info"
C_KEY_DDL_SRT = "ddl_srt"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class YoutubeTranscriptsFormDef(IStepFormDef):
    """Form definition for the YouTube transcripts step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_DDL

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by C_KEY_* constants.
        """
        self._build_subform_title(frame, widgets)
        self._build_subform_comment(frame, widgets)
        self._build_subform_options(frame, widgets)

    @staticmethod
    def _build_subform_title(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the title input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_TITLE tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Info/Titre :").pack(side="left", padx=(0, 5))
        title_var = tk.StringVar(value="Download automatique FRA/ENG")
        ttk.Entry(row0, textvariable=title_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_TITLE] = title_var

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

    @staticmethod
    def _build_subform_options(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the checkboxes row (basic_info / ddl_srt).

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_BASIC_INFO and C_KEY_DDL_SRT tk.BooleanVar.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        basic_info_var = tk.BooleanVar(value=True)
        CanvasCheckbox(row2, text="Récupérer la fiche", variable=basic_info_var).pack(side="left", padx=(0, 16))
        widgets[C_KEY_BASIC_INFO] = basic_info_var

        ddl_srt_var = tk.BooleanVar(value=True)
        CanvasCheckbox(row2, text="Récupérer les SRT", variable=ddl_srt_var).pack(side="left")
        widgets[C_KEY_DDL_SRT] = ddl_srt_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot.

        Args:
            params_dict: Serialised step parameters keyed by field name.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_TITLE].set(params_dict.get(C_KEY_TITLE, ""))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))
        widgets[C_KEY_BASIC_INFO].set(params_dict.get(C_KEY_BASIC_INFO, True))
        widgets[C_KEY_DDL_SRT].set(params_dict.get(C_KEY_DDL_SRT, True))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict.

        Args:
            widgets: Mapping of widget name to tk.Variable reference.

        Returns:
            Dictionary of step parameters ready for persistence in the model.
        """
        return {
            C_KEY_TITLE: widgets[C_KEY_TITLE].get().strip(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
            C_KEY_BASIC_INFO: widgets[C_KEY_BASIC_INFO].get(),
            C_KEY_DDL_SRT: widgets[C_KEY_DDL_SRT].get(),
        }


register_form(YoutubeTranscriptsFormDef())


# EOF
