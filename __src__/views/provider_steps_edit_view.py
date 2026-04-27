"""Provider workflow editor widgets.

This view is intentionally UI-only:
- it renders workflow controls,
- it renders a dynamic step form,
- it emits raw user payloads to callbacks.

Validation is handled outside of this view by presenter/domain layers.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, Optional, cast

from interfaces.base_step_form_interface import BaseStepFormInterface
from shared.step_types import STEP_TYPE_TO_LABEL
from views.step_forms.step_form_view_factory import StepFormViewFactory


class ProviderStepsEditView(ttk.Frame):
    """Renders workflow controls and delegates step payload collection."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)

        self._on_add_step: Optional[Callable[[str, Any], None]] = None
        self._on_edit_step: Optional[Callable[[], None]] = None
        self._on_delete_step: Optional[Callable[[], None]] = None
        self._on_move_up: Optional[Callable[[], None]] = None
        self._on_move_down: Optional[Callable[[], None]] = None
        self._on_clear_all: Optional[Callable[[], None]] = None

        self._workflow_items: list[Dict[str, Any]] = []
        self._form_factory = StepFormViewFactory()
        self._active_step_form: Optional[BaseStepFormInterface] = None

        self._label_to_type: dict[str, str] = {
            label: step_type for step_type, label in STEP_TYPE_TO_LABEL.items()
        }

        self._create_widgets()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1, uniform="workflow_instruction")
        self.columnconfigure(1, weight=1, uniform="workflow_instruction")
        self.rowconfigure(0, weight=1)

        self._build_workflow_panel()
        self._build_instruction_panel()
        self._render_instruction_form()

    def _build_workflow_panel(self) -> None:
        workflow_lf = ttk.LabelFrame(self, text="Workflow")
        workflow_lf.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        workflow_lf.columnconfigure(0, weight=1)
        workflow_lf.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(workflow_lf)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._list_steps = tk.Listbox(list_frame, exportselection=False, height=8)
        self._list_steps.grid(row=0, column=0, sticky="nsew")
        self._list_steps.bind("<<ListboxSelect>>", self._on_step_selection_changed)

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=cast(Callable[..., Any], self._list_steps.yview),
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._list_steps.configure(yscrollcommand=scrollbar.set)

        controls_frame = ttk.Frame(workflow_lf)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 8))
        controls_frame.columnconfigure(0, weight=1)

        left_controls = ttk.Frame(controls_frame)
        left_controls.grid(row=0, column=0, sticky="w")
        right_controls = ttk.Frame(controls_frame)
        right_controls.grid(row=0, column=1, sticky="e")

        self._btn_edit_step = ttk.Button(
            left_controls,
            text="Modifier",
            command=self._notify_edit_step,
            state=tk.DISABLED,
        )
        self._btn_edit_step.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_delete_step = ttk.Button(
            left_controls,
            text="Supprimer",
            command=self._notify_delete_step,
            state=tk.DISABLED,
        )
        self._btn_delete_step.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_move_up = ttk.Button(
            left_controls,
            text="Monter",
            command=self._notify_move_up,
            state=tk.DISABLED,
        )
        self._btn_move_up.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_move_down = ttk.Button(
            left_controls,
            text="Descendre",
            command=self._notify_move_down,
            state=tk.DISABLED,
        )
        self._btn_move_down.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_clear_all = ttk.Button(
            right_controls,
            text="Effacer tout",
            command=self._notify_clear_all,
        )
        self._btn_clear_all.pack(side=tk.RIGHT)

    def _build_instruction_panel(self) -> None:
        instruction_lf = ttk.LabelFrame(self, text="Instruction")
        instruction_lf.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        instruction_lf.columnconfigure(0, weight=1)
        instruction_lf.rowconfigure(1, weight=1)

        header = ttk.Frame(instruction_lf)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="Type:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._var_step_type = tk.StringVar(value="")
        self._cmb_step_type = ttk.Combobox(
            header,
            textvariable=self._var_step_type,
            values=[""] + list(self._label_to_type.keys()),
            state="readonly",
            width=28,
        )
        self._cmb_step_type.grid(row=0, column=1, sticky="ew")
        self._cmb_step_type.bind("<<ComboboxSelected>>", self._on_instruction_type_changed)

        self._instruction_form_frame = ttk.Frame(instruction_lf)
        self._instruction_form_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self._instruction_form_frame.columnconfigure(0, weight=1)

        footer = ttk.Frame(instruction_lf)
        footer.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))
        self._btn_add = ttk.Button(footer, text="Ajouter", command=self._notify_add_step)
        self._btn_add.pack(side=tk.RIGHT)

    def set_callbacks(
        self,
        on_add_step: Callable[[str, Any], None],
        on_edit_step: Callable[[], None],
        on_delete_step: Callable[[], None],
        on_move_up: Callable[[], None],
        on_move_down: Callable[[], None],
        on_clear_all: Callable[[], None],
    ) -> None:
        self._on_add_step = on_add_step
        self._on_edit_step = on_edit_step
        self._on_delete_step = on_delete_step
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_clear_all = on_clear_all

    def render_steps(self, workflow_items: list[Dict[str, Any]]) -> None:
        selected_index = self.get_selected_step_index()
        self._workflow_items = [dict(item) for item in workflow_items]

        self._list_steps.delete(0, tk.END)
        for item in self._workflow_items:
            self._list_steps.insert(tk.END, str(item.get("label", "")))

        if selected_index is not None and 0 <= selected_index < len(self._workflow_items):
            self._list_steps.selection_set(selected_index)

        self._update_step_buttons_state()

    def set_selected_step(self, index: int) -> None:
        self._list_steps.selection_clear(0, tk.END)

        if 0 <= index < self._list_steps.size():
            self._list_steps.selection_set(index)
            self._list_steps.activate(index)
            self._list_steps.see(index)

        self._update_step_buttons_state()

    def get_selected_step_index(self) -> Optional[int]:
        curselection_func = cast(Callable[[], tuple[int, ...]], self._list_steps.curselection)
        selected = curselection_func()
        if not selected:
            return None
        return selected[0]

    def _on_step_selection_changed(self, _event: tk.Event[tk.Widget]) -> None:
        self._update_step_buttons_state()

    def _update_step_buttons_state(self) -> None:
        selected_index = self.get_selected_step_index()
        total_steps = len(self._workflow_items)

        self._btn_edit_step.config(state=tk.NORMAL if selected_index is not None else tk.DISABLED)
        self._btn_delete_step.config(state=tk.NORMAL if selected_index is not None else tk.DISABLED)

        can_move_up = selected_index is not None and selected_index > 0
        can_move_down = selected_index is not None and selected_index < total_steps - 1
        self._btn_move_up.config(state=tk.NORMAL if can_move_up else tk.DISABLED)
        self._btn_move_down.config(state=tk.NORMAL if can_move_down else tk.DISABLED)

    def _notify_add_step(self) -> None:
        step_type = self._get_selected_step_type()
        if step_type is None:
            self._show_error("Veuillez sélectionner un type d'étape avant d'ajouter.")
            return

        if self._active_step_form is None:
            self._show_error("Le formulaire de l'étape n'est pas disponible.")
            return

        raw_step_value = self._active_step_form.get_data()
        if self._on_add_step:
            self._on_add_step(step_type, raw_step_value)

    def _notify_edit_step(self) -> None:
        if self._on_edit_step:
            self._on_edit_step()

    def _notify_delete_step(self) -> None:
        if self._on_delete_step:
            self._on_delete_step()

    def _notify_move_up(self) -> None:
        if self._on_move_up:
            self._on_move_up()

    def _notify_move_down(self) -> None:
        if self._on_move_down:
            self._on_move_down()

    def _notify_clear_all(self) -> None:
        if not self._workflow_items:
            return

        should_clear = messagebox.askyesno(
            "Effacer",
            "Voulez-vous supprimer toutes les étapes du workflow ?",
        )
        if not should_clear:
            return

        if self._on_clear_all:
            self._on_clear_all()

    def _on_instruction_type_changed(self, _event: tk.Event[tk.Widget]) -> None:
        self._render_instruction_form()

    def _render_instruction_form(self) -> None:
        for child in self._instruction_form_frame.winfo_children():
            child.destroy()
        self._active_step_form = None

        step_type = self._get_selected_step_type()
        if step_type is None:
            ttk.Label(
                self._instruction_form_frame,
                text="Sélectionnez un type d'étape pour afficher ses paramètres.",
            ).grid(row=0, column=0, sticky="w")
            return

        form = self._form_factory.create(self._instruction_form_frame, step_type=step_type)
        if form is None:
            ttk.Label(
                self._instruction_form_frame,
                text="Type d'étape non supporté.",
            ).grid(row=0, column=0, sticky="w")
            return

        form.grid(row=0, column=0, sticky="nsew")
        self._active_step_form = form

    def _get_selected_step_type(self) -> Optional[str]:
        return self._label_to_type.get(self._var_step_type.get())

    def _show_error(self, message: str) -> None:
        messagebox.showerror("Erreur", message)
