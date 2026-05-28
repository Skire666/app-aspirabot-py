"""IStepFormDef for CLOSE_TABS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, override

from interfaces.i_step_form_def import IStepFormDef
from models.step_scraping_model import StepScrapingModel
from shared.constants import C_MAXIMUM_NBR_TABS_BROWSER
from shared.enums import OpenUrlModeEnum, StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_registry import register_form
from views.steps._constants import safe_int_widget

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_INPUT_DEFAULT_FILTER_MODE: str = OpenUrlModeEnum.E_SOURCE.value
C_INPUT_IS_FILTER_CUSTOM: str = OpenUrlModeEnum.E_CUSTOM.value
C_INPUT_DEFAULT_MAX_TABS: int = 1

C_KEY_FILTER_MODE = "filter_mode"
C_KEY_FILTER_CUSTOM = "filter_custom"
C_KEY_MAX_TABS = "max_tabs"
C_KEY_COMMENT = "comment"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class CloseTabsFormDef(IStepFormDef):
    """Form definition for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLOSE_TABS

    @classmethod
    def label(cls) -> str:
        """Return the human-readable label for the step picker."""
        return C_STEP_TYPE_TO_LABELS.get(StepTypeEnum.E_CLOSE_TABS)

    @override
    def build_form(self, frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build all form widgets into the given frame.

        Args:
            frame: The tkinter frame to populate.
            widgets: Mutable mapping populated with tk.Variable references keyed by W_* constants.
        """
        self._build_subform_filters(frame, widgets)
        self._build_subform_max_tabs(frame, widgets)
        self._build_subform_comment(frame, widgets)

    @staticmethod
    def _build_subform_filters(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the URL filter mode radio buttons and custom filter entry row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with C_KEY_FILTER_MODE and C_KEY_FILTER_CUSTOM tk.Variables.
        """
        line1 = ttk.Frame(frame)
        line1.pack(fill="x", pady=(0, 8))

        filter_mode_var = tk.StringVar(value=C_INPUT_DEFAULT_FILTER_MODE)
        filter_url_var = tk.StringVar(value=".com")

        # Mode selection radio buttons
        CloseTabsFormDef._build_url_mode_buttons(line1, filter_mode_var)

        filter_url_entry = ttk.Entry(line1, textvariable=filter_url_var)
        filter_url_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_FILTER_MODE] = filter_mode_var
        widgets[C_KEY_FILTER_CUSTOM] = filter_url_var

        # Keep the entry state in sync with the selected mode
        CloseTabsFormDef._bind_url_mode_entry(filter_mode_var, filter_url_entry)

    @staticmethod
    def _build_url_mode_buttons(line1: ttk.Frame, filter_mode_var: tk.StringVar) -> None:
        """Build the URL filter mode radio buttons.

        Args:
            line1: Frame to pack the radio buttons into.
            filter_mode_var: StringVar that receives the selected mode value.
        """
        tk.Radiobutton(
            line1,
            text="Garder l'URL d'origine",
            variable=filter_mode_var,
            value=OpenUrlModeEnum.E_SOURCE.value,
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            line1,
            text="Filtre contenant",
            variable=filter_mode_var,
            value=OpenUrlModeEnum.E_CUSTOM.value,
        ).pack(side=tk.LEFT, padx=(0, 5))

    @staticmethod
    def _bind_url_mode_entry(filter_mode_var: tk.StringVar, filter_url_entry: ttk.Entry) -> None:
        """Synchronize the filter entry enabled state with the selected mode.

        Args:
            filter_mode_var: StringVar holding the current filter mode.
            filter_url_entry: Entry widget to enable or disable based on the mode.
        """

        def _sync_url_entry_state(*_args: object) -> None:
            state = "readonly" if filter_mode_var.get() == OpenUrlModeEnum.E_SOURCE.value else "normal"
            filter_url_entry.configure(state=state)

        # React to mode changes and initialize the current state
        filter_mode_var.trace_add("write", _sync_url_entry_state)
        _sync_url_entry_state()

    @staticmethod
    def _build_subform_max_tabs(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the maximum open tabs spinbox row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_MAX_TABS tk.Variable.
        """
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 8))

        ttk.Label(row1, text="Max. onglets ouverts:").pack(side="left", padx=(0, 5))
        max_var = tk.StringVar(value=str(C_INPUT_DEFAULT_MAX_TABS))
        ttk.Spinbox(row1, from_=1, to=C_MAXIMUM_NBR_TABS_BROWSER, textvariable=max_var, width=7).pack(
            side="left", padx=(0, 5),
        )
        widgets[C_KEY_MAX_TABS] = max_var

    @staticmethod
    def _build_subform_comment(frame: ttk.Frame, widgets: dict[str, Any]) -> None:
        """Build the comment input row.

        Args:
            frame: Parent frame to pack the row into.
            widgets: Mutable mapping; populated with the C_KEY_COMMENT tk.Variable.
        """
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 8))

        ttk.Label(row2, text="Commentaire :").pack(side="left", padx=(0, 5))
        comm_var = tk.StringVar(value="")
        ttk.Entry(row2, textvariable=comm_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        widgets[C_KEY_COMMENT] = comm_var

    @override
    def load_params_step_to_widget(self, model: StepScrapingModel, widgets: dict[str, Any]) -> None:
        """Load step parameters from the model into form widgets.

        Args:
            model: The step model containing stored parameters.
            widgets: Mutable mapping of widget name to tk.Variable reference.
        """
        widgets[C_KEY_FILTER_MODE].set(model.params.get(C_KEY_FILTER_MODE, OpenUrlModeEnum.E_SOURCE.value))
        widgets[C_KEY_FILTER_CUSTOM].set(model.params.get(C_KEY_FILTER_CUSTOM, ""))
        widgets[C_KEY_MAX_TABS].set(str(model.params.get(C_KEY_MAX_TABS, C_INPUT_DEFAULT_MAX_TABS)))
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
            C_KEY_FILTER_MODE: widgets[C_KEY_FILTER_MODE].get(),
            C_KEY_FILTER_CUSTOM: widgets[C_KEY_FILTER_CUSTOM].get().strip(),
            C_KEY_MAX_TABS: safe_int_widget(widgets, C_KEY_MAX_TABS, -1),
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
        max_tabs = model.params.get(C_KEY_MAX_TABS, C_INPUT_DEFAULT_MAX_TABS)

        # Custom filter mode includes the filter pattern in the label
        if model.params.get(C_KEY_FILTER_MODE) == C_INPUT_IS_FILTER_CUSTOM:
            filter_custom = model.params.get(C_KEY_FILTER_CUSTOM, "")
            return f"Fermer les onglets  -  {max_tabs} onglet(s) max.\nFiltre URL : *{filter_custom}*"
        return f"Fermer les onglets  -  {max_tabs} onglet(s) max.\nFiltre : Garde l'URL de départ."


register_form(CloseTabsFormDef())

# EOF
