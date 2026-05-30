"""IStepFormDef for CLICK_FOR_DOWNLOAD."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, cast, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from models.steps.click_for_download_params import ClickForDownloadParams
from models.steps_context_model import StepsContext
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import CLICK_MODES

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"

C_KEY_SELECTOR = "selector"
C_KEY_CLICK_MODE = "click_mode"
C_KEY_INDEX_CLICKED = "index_clicked"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ClickForDownloadFormDef(IStepFormDef):
    """Form definition for the click for download scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLICK_FOR_DOWNLOAD

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_CLICK_FOR_DOWNLOAD)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_selector(frame, widgets)
        self._build_subform_click_mode(frame, widgets)
        self._build_subform_index_clicked(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_selector(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the CSS selector input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_SELECTOR tk.Variable.
        """
        row0 = ttk.Frame(frame)
        row0.pack(fill="x", pady=(0, 8))

        ttk.Label(row0, text="Sélecteur CSS :").pack(side=tk.LEFT, padx=(0, 5))
        sel_var = tk.StringVar(value=C_INPUT_DEFAULT_CSS_SELECTOR)
        ttk.Entry(row0, textvariable=sel_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_SELECTOR] = sel_var

    @staticmethod
    def _build_subform_click_mode(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the click mode selector row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_CLICK_MODE tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Type de clic à utiliser (est cumulatif) :").pack(side=tk.LEFT, padx=(0, 5))
        mode_var = tk.StringVar(value="Normal")
        ttk.Combobox(row1, textvariable=mode_var, values=CLICK_MODES, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5),
        )
        widgets[C_KEY_CLICK_MODE] = mode_var

    @staticmethod
    def _build_subform_index_clicked(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the index clicked input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_INDEX_CLICKED tk.Variable.
        """
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))

        ttk.Label(row3, text="Index à cliquer (1 seul clique) :").pack(side=tk.LEFT, padx=(0, 5))
        index_var = tk.IntVar(value=0)
        ttk.Entry(row3, textvariable=index_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_INDEX_CLICKED] = index_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row2, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        p = cast(ClickForDownloadParams, model.params)
        widgets[C_KEY_SELECTOR].set(p.selector)
        widgets[C_KEY_CLICK_MODE].set(p.click_mode)
        widgets[C_KEY_INDEX_CLICKED].set(p.index_clicked)
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
            C_KEY_SELECTOR: widgets[C_KEY_SELECTOR].get().strip(),
            C_KEY_CLICK_MODE: widgets[C_KEY_CLICK_MODE].get(),
            C_KEY_INDEX_CLICKED: widgets[C_KEY_INDEX_CLICKED].get(),
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
        p = cast(ClickForDownloadParams, model.params)
        selector = p.selector or "<vide>"
        index_clicked = p.index_clicked
        return f"Cliquer pour télécharger  -  Index {index_clicked}\nSél. : {selector}"


register_form(ClickForDownloadFormDef())

# EOF
