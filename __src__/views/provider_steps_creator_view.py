"""Provider step editor dialog utilities.

This dialog is UI-only and returns raw user payloads.
Validation is handled by presenter/domain layers.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from interfaces.base_step_form_interface import BaseStepFormInterface
from models.step_scrapping_model import StepType
from views.step_forms.step_form_view_factory import StepFormViewFactory


class ProviderStepsCreatorView:
    """Modal dialog used to create/edit a provider step payload."""

    def __init__(self, parent: tk.Widget, type_to_label: dict[StepType, str]) -> None:
        self._parent = parent
        self._type_to_label = dict(type_to_label)
        self._form_factory = StepFormViewFactory()

    def open_step_dialog(self, step_type: StepType, initial_value: Any = None) -> tuple[bool, Any]:
        """Opens a step dialog and returns raw form payload."""
        if step_type not in self._type_to_label:
            self._show_invalid_type_error()
            return False, None

        dialog = tk.Toplevel(self._parent)
        dialog.title(self._type_to_label[step_type])
        dialog.transient(self._parent.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)

        content = ttk.Frame(dialog, padding=12)
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)

        form = self._form_factory.create(content, step_type=step_type, initial_value=initial_value)
        if form is None:
            dialog.destroy()
            self._show_invalid_type_error()
            return False, None

        form.grid(row=0, column=0, sticky="nsew")

        result: dict[str, Any] = {"submitted": False, "value": None}
        self._create_footer(content, dialog, form, result)

        self._parent.wait_window(dialog)
        if not bool(result["submitted"]):
            return False, None
        return True, result["value"]

    def _create_footer(
        self,
        content: ttk.Frame,
        dialog: tk.Toplevel,
        form: BaseStepFormInterface,
        result: dict[str, Any],
    ) -> None:
        buttons = ttk.Frame(content)
        buttons.grid(row=1, column=0, sticky="e", pady=(8, 0))

        def submit() -> None:
            result["value"] = form.get_data()
            result["submitted"] = True
            dialog.destroy()

        ttk.Button(buttons, text="Annuler", command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Valider", command=submit).pack(side=tk.RIGHT)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def _show_invalid_type_error(self) -> None:
        messagebox.showerror("Erreur", "Type d'étape invalide.")
