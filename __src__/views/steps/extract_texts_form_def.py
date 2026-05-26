"""IStepFormDef for EXTRACT_TEXT."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import (
    EXTRACT_MODE_DISPLAY,
    EXTRACT_MODE_MODEL_TO_VIEW,
    EXTRACT_MODE_VIEW_TO_MODEL,
    EXTRACT_TARGET_DISPLAY,
    EXTRACT_TARGET_MODEL_TO_VIEW,
    EXTRACT_TARGET_VIEW_TO_MODEL,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_CSS_SELECTOR = "Cf. FAQ ou 'copy selector' dans chrome/debug"

C_KEY_SELECTOR = "selector"
C_KEY_EXTRACT_MODE = "extract_mode"
C_KEY_TARGET_EXTRACTED = "target"
C_KEY_MAPPING = "mapping"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ExtractTextsFormDef(IStepFormDef):
    """Form definition for the extract text scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXTRACT_TEXTS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_EXTRACT_TEXTS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_selector(frame, widgets)
        self._build_subform_extract_mode(frame, widgets)
        self._build_subform_target(frame, widgets)
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
    def _build_subform_extract_mode(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the extraction mode combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_EXTRACT_MODE tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Mode d'extraction :").pack(side=tk.LEFT, padx=(0, 5))
        mode_var = tk.StringVar(value=EXTRACT_MODE_DISPLAY[0])
        ttk.Combobox(row1, textvariable=mode_var, values=EXTRACT_MODE_DISPLAY, state="readonly").pack(
            side=tk.LEFT, fill="x", expand=True, padx=(0, 5)
        )
        widgets[C_KEY_EXTRACT_MODE] = mode_var

    @staticmethod
    def _build_subform_target(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the extraction target combobox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_TARGET_EXTRACTED tk.Variable.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Cible :").pack(side=tk.LEFT, padx=(0, 5))
        target_var = tk.StringVar(value=EXTRACT_TARGET_DISPLAY[-1])
        ttk.Combobox(row2, textvariable=target_var, values=EXTRACT_TARGET_DISPLAY, state="readonly").pack(
            side=tk.LEFT, padx=(0, 30)
        )
        widgets[C_KEY_TARGET_EXTRACTED] = target_var

        ttk.Label(row2, text="Clé/Mapping :").pack(side=tk.LEFT, padx=(0, 5))
        mapping_var = tk.StringVar(value="key_name")
        ttk.Entry(row2, textvariable=mapping_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_MAPPING] = mapping_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=(0, 8))

        ttk.Label(row3, text="Commentaire :").pack(side=tk.LEFT, padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=comm_var).pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_SELECTOR].set(model.params.get(C_KEY_SELECTOR, ""))
        widgets[C_KEY_EXTRACT_MODE].set(
            EXTRACT_MODE_MODEL_TO_VIEW.get(model.params.get(C_KEY_EXTRACT_MODE, "innerText"), EXTRACT_MODE_DISPLAY[0])
        )
        widgets[C_KEY_TARGET_EXTRACTED].set(
            EXTRACT_TARGET_MODEL_TO_VIEW.get(
                model.params.get(C_KEY_TARGET_EXTRACTED, "first"), EXTRACT_TARGET_DISPLAY[-1]
            )
        )
        widgets[C_KEY_MAPPING].set(model.params.get(C_KEY_MAPPING, "key_name"))
        widgets[C_KEY_COMMENT].set(model.params.get(C_KEY_COMMENT, ""))

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
            C_KEY_EXTRACT_MODE: EXTRACT_MODE_VIEW_TO_MODEL.get(widgets[C_KEY_EXTRACT_MODE].get()),
            C_KEY_TARGET_EXTRACTED: EXTRACT_TARGET_VIEW_TO_MODEL.get(widgets[C_KEY_TARGET_EXTRACTED].get()),
            C_KEY_MAPPING: widgets[C_KEY_MAPPING].get().strip(),
            C_KEY_COMMENT: widgets[C_KEY_COMMENT].get().strip(),
        }

    @override
    def format_label(self, model: StepScrapingModel, idx: int) -> str:
        """Return a compact human-readable label for this step instance.

        Args:
            model: The step model containing current parameters.
            idx: Zero-based index of this step in the workflow.

        Returns:
            A two-line string suitable for display in the steps list.
        """
        selector = model.params.get(C_KEY_SELECTOR, "<vide>")
        extract_mode = model.params.get(C_KEY_EXTRACT_MODE, "")
        target = model.params.get(C_KEY_TARGET_EXTRACTED, "")
        mapping = model.params.get(C_KEY_MAPPING, "")
        return f"Extraire textes  -  {mapping}\n{extract_mode}  /  {target}  |  Sél. : {selector}"


register_form(ExtractTextsFormDef())
