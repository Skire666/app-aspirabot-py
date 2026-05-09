"""Inline form panel for creating and editing a scraping step.

This ttk.LabelFrame is embedded inside WorkflowBuilderView. It displays
a type selector and a dynamic form area rebuilt whenever the step type changes.
Form building, loading, reading and validation are fully delegated to the
registered IStepFormDef instance for the active step type.

Example:
    >>> panel = StepInlineFormPanel(parent_frame)
    >>> panel.on_confirm = lambda step: print(step)
    >>> panel.on_cancel = lambda: print("cancelled")
    >>> panel.load(existing_step)
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from models.step_scraping_model import StepScrapingModel, StepType
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.random_util import generate_rng_id_step
from shared.step_registry import get_form

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Reverse mapping for label → StepType lookup.
_LABEL_TO_TYPE: dict[str, StepType] = {v: k for k, v in C_STEP_TYPE_TO_LABELS.items()}


## ---------------------------------------------------------------------------
## Panel
## ---------------------------------------------------------------------------


class StepInlineFormPanel(ttk.Frame):
    """Inline form panel for creating or editing a single scraping step.

    All form-specific logic (build / load / read / validate / label) is
    delegated to the IStepFormDef registered for the active StepType.  The
    panel owns only the container frame and the shared widget dict.

    Attributes:
        on_confirm: Callback(StepScrapingModel) fired when step is validated.
        on_cancel: Callback fired when the user cancels without changes.
        on_type_changed: Callback(label: str) fired when step type changes.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the panel and builds all sub-regions.

        Args:
            parent: The parent Tkinter widget to embed into.
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.on_confirm: Callable[[StepScrapingModel], None] | None = None
        self.on_cancel: Callable[[], None] | None = None
        self.on_type_changed: Callable[[str], None] | None = None
        self._type_var = tk.StringVar()
        self._form_widgets: dict[str, Any] = {}
        self._step_selected: StepScrapingModel | None = None
        # Available steps for JUMP_TO_STEP target population.
        self._available_steps: list[StepScrapingModel] = []
        self._create_widgets()

    # ---------------------------------------------------------------
    # Widget construction
    # ---------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Builds type selector, dynamic form area, error label, and buttons.

        Pack order rule: BOTTOM widgets must be packed before TOP ones so that
        pack reserves their space before the expanding form_frame claims the rest.
        """
        top_area = ttk.Frame(self)
        top_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5)

        self._form_frame = ttk.Frame(top_area)
        self._form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 5), pady=5)
        self._create_bottom()

    def _create_bottom(self) -> None:
        """Creates the Confirm and Cancel buttons at the bottom."""
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self._btn_create = ttk.Button(btn_frame, text="Ajouter une étape", command=self._btn_confirm_create)
        self._btn_create.pack(side=tk.LEFT, padx=5)
        self._btn_edit = ttk.Button(btn_frame, text="Modifier l'étape", command=self._btn_confirm_update)
        self._btn_edit.pack(side=tk.LEFT, padx=5)
        self._btn_cancel = ttk.Button(btn_frame, text="Annuler", command=self._btn_cancel_edition)
        self._btn_cancel.pack(side=tk.LEFT, padx=5)
        self._error_label = ttk.Label(btn_frame, text="", foreground="red")
        self._error_label.pack(side=tk.RIGHT, fill=tk.X, padx=(10, 5), pady=(0, 2))
        self.set_creation_mode()

    # ---------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------

    def set_creation_mode(self) -> None:
        """Enables Create; disables Edit and Cancel."""
        self._btn_create.configure(state="normal")
        self._btn_create.pack(side=tk.LEFT, padx=5)  # Show Create button in creation mode
        self._btn_edit.configure(state="disabled")
        self._btn_edit.pack_forget()  # Edit button is hidden in creation mode
        self._btn_cancel.configure(state="disabled")
        self._btn_cancel.pack_forget()  # Edit button is hidden in creation mode

    def set_edit_mode(self) -> None:
        """Enables Edit and Cancel; disables Create."""
        self._btn_create.configure(state="disabled")
        self._btn_create.pack_forget()
        self._btn_edit.configure(state="normal")
        self._btn_edit.pack(side=tk.LEFT, padx=5)  # Show Edit button in edit mode
        self._btn_cancel.configure(state="normal")
        self._btn_cancel.pack(side=tk.LEFT, padx=5)  # Show Edit button in edit mode

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        """Stores the workflow step list for JUMP_TO_STEP target population.

        Args:
            steps: Current ordered workflow step list.
        """
        self._available_steps = list(steps)
        self._form_widgets["_all_steps_available"] = self._available_steps

    def load(self, step: StepScrapingModel | None = None) -> None:
        """Prepares the form for a new step or pre-fills it from an existing one.

        Args:
            step: Existing step to pre-fill, or None to show a blank form.
        """
        initial_type = step.step_type if step else StepType.OPEN_URL

        label = C_STEP_TYPE_TO_LABELS[initial_type]
        self._type_var.set(label)
        self._rebuild_form(initial_type)

        self._step_selected = step
        if step:
            self._load_step(step)

        if self.on_type_changed:
            self.on_type_changed(label)

    # ---------------------------------------------------------------
    # Dynamic form management
    # ---------------------------------------------------------------

    def _on_type_changed(self, event: tk.Event) -> None:
        """Rebuilds the form area when the type selector changes."""
        label = self._type_var.get()
        step_type = _LABEL_TO_TYPE.get(label)
        if step_type is not None:
            self._rebuild_form(step_type)
        if self.on_type_changed and label:
            self.on_type_changed(label)

    def _rebuild_form(self, step_type: StepType) -> None:
        """Clears and rebuilds the dynamic form via the registered IStepFormDef."""
        for widget in self._form_frame.winfo_children():
            widget.destroy()
        self._form_widgets.clear()
        self._error_label.configure(text="")

        # Inject JUMP_TO_STEP context before building so the form def can
        # populate the target combobox from the available steps list.
        self._form_widgets["_all_steps_available"] = self._available_steps
        self._logger.debug(f"Rebuilding form for step type {step_type} with steps={len(self._available_steps)}")

        try:
            if step_type is not None and step_type != StepType.UNSET:
                get_form(step_type).build_form(self._form_frame, self._form_widgets)
        except ValueError:
            pass

    # ---------------------------------------------------------------
    # Pre-fill and read-back — fully delegated to form defs
    # ---------------------------------------------------------------

    def _load_step(self, step: StepScrapingModel) -> None:
        """Pre-fills form widgets from an existing step's params."""
        try:
            get_form(step.step_type).load_params_step_to_widget(step.params, self._form_widgets)
        except ValueError:
            pass

    def _get_params(self, step_type: StepType) -> dict[str, Any]:
        """Reads current widget values and returns the params dict."""
        try:
            return get_form(step_type).read_params_from_view(self._form_widgets)
        except ValueError:
            return {}

    # ---------------------------------------------------------------
    # Validation — delegated to form defs
    # ---------------------------------------------------------------

    def _validate_form(self, step_type: StepType) -> list[str]:
        """Validates the current form for the given step type."""
        try:
            return get_form(step_type).validate_form(self._form_widgets)
        except ValueError:
            return []

    # ---------------------------------------------------------------
    # Button handlers
    # ---------------------------------------------------------------

    def _btn_confirm_create(self) -> None:
        """Validates the form, builds the step, and fires on_confirm."""
        label = self._type_var.get()
        step_type = _LABEL_TO_TYPE.get(label)
        if step_type is None:
            return

        errors = self._validate_form(step_type)
        if errors:
            self._error_label.configure(text=errors[0])
            return

        self._error_label.configure(text="")
        params = self._get_params(step_type)

        step = StepScrapingModel(
            step_type=step_type,
            is_active=True,
            step_id=generate_rng_id_step(),
            params=params,
            parent_context=self._available_steps,
        )
        if self.on_confirm:
            self.on_confirm(step)

    def _btn_confirm_update(self) -> None:
        """Validates the form, builds the step, and fires on_confirm."""
        label = self._type_var.get()
        step_type = _LABEL_TO_TYPE.get(label)
        if step_type is None:
            return

        errors = self._validate_form(step_type)
        if errors:
            self._error_label.configure(text=errors[0])
            return

        self._error_label.configure(text="")
        params = self._get_params(step_type)

        step = StepScrapingModel(
            step_type=step_type,
            is_active=self._step_selected.is_active,
            step_id=self._step_selected.step_id,
            params=params,
            parent_context=self._available_steps,
        )
        if self.on_confirm:
            self.on_confirm(step)

    def _btn_cancel_edition(self) -> None:
        """Fires the on_cancel callback without modifying the step list."""
        if self.on_cancel:
            self.on_cancel()
