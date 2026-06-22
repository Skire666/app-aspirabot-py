"""IStepFormDef for YOUTUBE_SUBTITLES."""

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

C_KEY_DOWNLOAD_FRA_SRT = "download_fra_srt"
C_KEY_DOWNLOAD_ENG_SRT = "download_eng_srt"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class YoutubeSubtitlesFormDef(IStepFormDef):
    """Form definition for the YouTube subtitles step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_YOUTUBE_SUBTITLES

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame."""
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        fra_var = tk.BooleanVar(value=True)
        CanvasCheckbox(line1, text="Télécharger SRT Français (FRA)", variable=fra_var).pack(side=tk.LEFT)
        widgets[C_KEY_DOWNLOAD_FRA_SRT] = fra_var

        line2 = ttk.Frame(frame)
        line2.pack(fill="x", pady=(0, 8))

        eng_var = tk.BooleanVar(value=True)
        CanvasCheckbox(line2, text="Télécharger SRT Anglais (ENG)", variable=eng_var).pack(side=tk.LEFT)
        widgets[C_KEY_DOWNLOAD_ENG_SRT] = eng_var

        line3 = ttk.Frame(frame)
        line3.pack(fill="x", pady=(0, 8))

        ttk.Label(line3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(line3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, params_dict: dict[str, Any], widgets: dict[str, Any]) -> None:
        """Pre-fill form widgets from a serialised params snapshot."""
        widgets[C_KEY_DOWNLOAD_FRA_SRT].set(bool(params_dict.get(C_KEY_DOWNLOAD_FRA_SRT, True)))
        widgets[C_KEY_DOWNLOAD_ENG_SRT].set(bool(params_dict.get(C_KEY_DOWNLOAD_ENG_SRT, True)))
        widgets[C_KEY_COMMENT].set(params_dict.get(C_KEY_COMMENT, ""))

    @override
    def read_params_from_view(self, widgets: dict[str, Any]) -> dict[str, Any]:
        """Read current widget values and return them as a step parameters dict."""
        return {
            C_KEY_DOWNLOAD_FRA_SRT: widgets[C_KEY_DOWNLOAD_FRA_SRT].get(),
            C_KEY_DOWNLOAD_ENG_SRT: widgets[C_KEY_DOWNLOAD_ENG_SRT].get(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }


register_form(YoutubeSubtitlesFormDef())


# EOF
