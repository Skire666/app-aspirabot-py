"""Provider workflow and instruction editor widgets.

This module contains a dedicated Tkinter sub-view used by the provider edit
screen. It renders:
1. The workflow list with move/edit/delete controls.
2. A dynamic instruction form that changes according to the selected step type.

The class is intentionally UI-focused and delegates business actions through
callbacks to keep MVP responsibilities clear.

Example:
    root = tk.Tk()
    steps_view = ProviderStepsEditView(root)
    steps_view.set_callbacks(
        on_add_step=lambda step_type, value: print(step_type, value),
        on_edit_step=lambda: None,
        on_delete_step=lambda: None,
        on_move_up=lambda: None,
        on_move_down=lambda: None,
        on_clear_all=lambda: None,
    )
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, Optional, cast


class ProviderStepsEditView(ttk.Frame):
    """Renders workflow controls and a dynamic step-instruction form.

    Args:
        parent: Parent Tk widget that owns this frame.

    Raises:
        tk.TclError: If Tkinter cannot create one of the underlying widgets.

    Example:
        view = ProviderStepsEditView(parent=root)
        view.render_steps([{"label": "Open URL"}, {"label": "Wait"}])
    """

    ADD_OPTIONS: dict[str, str] = {
        "Ouvrir une URL": "open_url",
        "Attendre X secondes": "wait_seconds",
        "Rafraichir page": "refresh_page",
        "Télécharger une image": "download_image",
        "Vérifier image par taille": "check_if_image_here",
        "Cliquer sur un élément": "click_element",
    }

    WAIT_UNIT_MAP: dict[str, str] = {
        "heure": "hours",
        "minute": "minutes",
        "seconde": "seconds",
        "milli-sec": "milliseconds",
    }

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes state and builds all widgets.

        Args:
            parent: Parent Tk widget that contains this frame.

        Returns:
            None.

        Raises:
            tk.TclError: If widget creation fails.
        """
        super().__init__(parent)

        # Store callback hooks set by the parent presenter/view.
        self._on_add_step: Optional[Callable[[str, Any], None]] = None
        self._on_edit_step: Optional[Callable[[], None]] = None
        self._on_delete_step: Optional[Callable[[], None]] = None
        self._on_move_up: Optional[Callable[[], None]] = None
        self._on_move_down: Optional[Callable[[], None]] = None
        self._on_clear_all: Optional[Callable[[], None]] = None

        # Keep currently displayed workflow and form variables.
        self._workflow_items: list[Dict[str, Any]] = []
        self._instruction_form_vars: dict[str, Any] = {}

        # Build visual structure and default form.
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Creates the full two-column UI layout.

        Returns:
            None.

        Raises:
            tk.TclError: If one of the child widget creations fails.
        """
        # Configure top-level geometry first.
        self._configure_layout()

        # Build workflow and instruction panels.
        self._build_workflow_panel()
        self._build_instruction_panel()

        # Render the default placeholder form.
        self._render_instruction_form()

    def _configure_layout(self) -> None:
        """Configures frame grid layout for 50/50 columns.

        Returns:
            None.

        Raises:
            None.
        """
        # Keep workflow and instruction widths balanced.
        self.columnconfigure(0, weight=1, uniform="workflow_instruction")
        self.columnconfigure(1, weight=1, uniform="workflow_instruction")

        # Allow vertical expansion.
        self.rowconfigure(0, weight=1)

    def _build_workflow_panel(self) -> None:
        """Builds the workflow panel and its sub-controls.

        Returns:
            None.

        Raises:
            tk.TclError: If panel widget creation fails.
        """
        # Create the workflow container.
        workflow_lf = ttk.LabelFrame(self, text="Workflow")
        workflow_lf.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        workflow_lf.columnconfigure(0, weight=1)
        workflow_lf.rowconfigure(0, weight=1)

        # Populate list and action controls.
        self._build_workflow_list(workflow_lf)
        self._build_workflow_controls(workflow_lf)

    def _build_workflow_list(self, parent: ttk.LabelFrame) -> None:
        """Builds the listbox area used to display workflow steps.

        Args:
            parent: Parent label frame hosting the list widgets.

        Returns:
            None.

        Raises:
            tk.TclError: If listbox or frame creation fails.
        """
        # Place a dedicated frame for list and scrollbar.
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Create the selectable list and bind selection updates.
        self._list_steps = tk.Listbox(list_frame, exportselection=False, height=8)
        self._list_steps.grid(row=0, column=0, sticky="nsew")
        self._list_steps.bind("<<ListboxSelect>>", self._on_step_selection_changed)

        # Attach vertical scrolling behavior.
        self._attach_workflow_scrollbar(list_frame)

    def _attach_workflow_scrollbar(self, list_frame: ttk.Frame) -> None:
        """Attaches a vertical scrollbar to the workflow listbox.

        Args:
            list_frame: Frame hosting the listbox and scrollbar.

        Returns:
            None.

        Raises:
            tk.TclError: If scrollbar creation fails.
        """
        # Build scrollbar and connect it to listbox yview.
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=cast(Callable[..., Any], getattr(self._list_steps, "yview")),
        )
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Connect listbox-to-scrollbar feedback.
        self._list_steps.configure(yscrollcommand=scrollbar.set)

    def _build_workflow_controls(self, parent: ttk.LabelFrame) -> None:
        """Builds step action controls under the workflow list.

        Args:
            parent: Parent label frame hosting the controls.

        Returns:
            None.

        Raises:
            tk.TclError: If control widgets cannot be created.
        """
        # Create a two-zone control row.
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 8))
        controls_frame.columnconfigure(0, weight=1)

        # Left side contains move/edit/delete actions.
        left_controls = ttk.Frame(controls_frame)
        left_controls.grid(row=0, column=0, sticky="w")

        # Right side contains clear-all action.
        right_controls = ttk.Frame(controls_frame)
        right_controls.grid(row=0, column=1, sticky="e")

        # Build both control groups.
        self._build_left_controls(left_controls)
        self._build_right_controls(right_controls)

    def _build_left_controls(self, parent: ttk.Frame) -> None:
        """Builds edit/delete/reorder buttons.

        Args:
            parent: Frame hosting the left control buttons.

        Returns:
            None.

        Raises:
            tk.TclError: If button creation fails.
        """
        # Keep buttons disabled until a step is selected.
        self._btn_edit_step = ttk.Button(
            parent,
            text="Modifier",
            command=self._notify_edit_step,
            state=tk.DISABLED,
        )
        self._btn_edit_step.pack(side=tk.LEFT, padx=(0, 6))

        # Delete selected step.
        self._btn_delete_step = ttk.Button(
            parent,
            text="Supprimer",
            command=self._notify_delete_step,
            state=tk.DISABLED,
        )
        self._btn_delete_step.pack(side=tk.LEFT, padx=(0, 6))

        # Move selected step up and down.
        self._btn_move_up = ttk.Button(
            parent,
            text="Monter",
            command=self._notify_move_up,
            state=tk.DISABLED,
        )
        self._btn_move_up.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_move_down = ttk.Button(
            parent,
            text="Descendre",
            command=self._notify_move_down,
            state=tk.DISABLED,
        )
        self._btn_move_down.pack(side=tk.LEFT, padx=(0, 6))

    def _build_right_controls(self, parent: ttk.Frame) -> None:
        """Builds the clear-all workflow button.

        Args:
            parent: Frame hosting the right control button.

        Returns:
            None.

        Raises:
            tk.TclError: If button creation fails.
        """
        # Clear all steps from workflow.
        self._btn_clear_all = ttk.Button(
            parent,
            text="Effacer tout",
            command=self._notify_clear_all,
        )
        self._btn_clear_all.pack(side=tk.RIGHT)

    def _build_instruction_panel(self) -> None:
        """Builds the instruction panel and its sections.

        Returns:
            None.

        Raises:
            tk.TclError: If panel creation fails.
        """
        # Create panel container for dynamic step parameters.
        instruction_lf = ttk.LabelFrame(self, text="Instruction")
        instruction_lf.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        instruction_lf.columnconfigure(0, weight=1)
        instruction_lf.rowconfigure(1, weight=1)

        # Build header, dynamic form area, and footer button.
        self._build_instruction_header(instruction_lf)
        self._build_instruction_form_frame(instruction_lf)
        self._build_instruction_footer(instruction_lf)

    def _build_instruction_header(self, parent: ttk.LabelFrame) -> None:
        """Builds instruction header and step-type selector.

        Args:
            parent: Instruction panel container.

        Returns:
            None.

        Raises:
            tk.TclError: If combobox or labels fail to initialize.
        """
        # Header frame stores type label and combobox.
        header = ttk.Frame(parent)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header.columnconfigure(1, weight=1)

        # Build step type selector with all supported options.
        ttk.Label(header, text="Type:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._var_step_type = tk.StringVar(value="Sélectionner...")
        options = ["Sélectionner..."] + list(self.ADD_OPTIONS.keys())
        self._cmb_step_type = ttk.Combobox(
            header,
            textvariable=self._var_step_type,
            values=options,
            state="readonly",
            width=28,
        )
        self._cmb_step_type.grid(row=0, column=1, sticky="ew")

        # Re-render form when type changes.
        self._cmb_step_type.bind(
            "<<ComboboxSelected>>",
            self._on_instruction_type_changed,
        )

    def _build_instruction_form_frame(self, parent: ttk.LabelFrame) -> None:
        """Builds the frame where dynamic form widgets are rendered.

        Args:
            parent: Instruction panel container.

        Returns:
            None.

        Raises:
            tk.TclError: If frame creation fails.
        """
        # This frame is cleared and rebuilt when step type changes.
        self._instruction_form_frame = ttk.Frame(parent)
        self._instruction_form_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        # Column 0 allows placeholder labels to expand.
        self._instruction_form_frame.columnconfigure(0, weight=1)

    def _build_instruction_footer(self, parent: ttk.LabelFrame) -> None:
        """Builds instruction footer with the add button.

        Args:
            parent: Instruction panel container.

        Returns:
            None.

        Raises:
            tk.TclError: If footer widgets cannot be created.
        """
        # Footer row aligns "Add" action to the right.
        footer = ttk.Frame(parent)
        footer.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))

        # The button delegates behavior through callbacks.
        self._btn_add = ttk.Button(
            footer,
            text="Ajouter",
            command=self._notify_add_step,
        )
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
        """Sets callback hooks used by the parent presenter/view chain.

        Args:
            on_add_step: Called when a new step is validated.
            on_edit_step: Called when the user requests to edit selected step.
            on_delete_step: Called when the user requests to delete selected step.
            on_move_up: Called when selected step should move up.
            on_move_down: Called when selected step should move down.
            on_clear_all: Called when all workflow steps should be cleared.

        Returns:
            None.

        Raises:
            None.
        """
        # Store callback references for later UI events.
        self._on_add_step = on_add_step
        self._on_edit_step = on_edit_step
        self._on_delete_step = on_delete_step
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_clear_all = on_clear_all

    def render_steps(self, workflow_items: list[Dict[str, Any]]) -> None:
        """Renders the workflow list and preserves current selection if possible.

        Args:
            workflow_items: Ordered step descriptors containing at least a
                ``label`` key used for listbox display.

        Returns:
            None.

        Raises:
            tk.TclError: If listbox operations fail.
        """
        # Save current selection before refreshing items.
        selected_index = self.get_selected_step_index()
        self._workflow_items = [dict(item) for item in workflow_items]

        # Rebuild displayed rows from the latest workflow state.
        self._list_steps.delete(0, tk.END)
        for item in self._workflow_items:
            self._list_steps.insert(tk.END, str(item.get("label", "")))

        # Restore previous index when still valid.
        if selected_index is not None and 0 <= selected_index < len(self._workflow_items):
            self._list_steps.selection_set(selected_index)

        # Recompute button availability after refresh.
        self._update_step_buttons_state()

    def set_selected_step(self, index: int) -> None:
        """Selects a workflow row by index and updates controls.

        Args:
            index: Zero-based list index to select.

        Returns:
            None.

        Raises:
            tk.TclError: If listbox selection operations fail.
        """
        # Reset existing selection first.
        self._list_steps.selection_clear(0, tk.END)

        # Select and reveal item only when index is in range.
        if 0 <= index < self._list_steps.size():
            self._list_steps.selection_set(index)
            self._list_steps.activate(index)
            self._list_steps.see(index)

        # Keep action buttons in sync with current selection.
        self._update_step_buttons_state()

    def get_selected_step_index(self) -> Optional[int]:
        """Returns selected workflow index if a row is currently selected.

        Returns:
            Optional[int]: The selected index, or ``None`` if nothing is selected.

        Raises:
            None.
        """
        # Read listbox selection tuple safely.
        curselection_func = cast(
            Callable[[], tuple[int, ...]],
            getattr(self._list_steps, "curselection"),
        )
        selected = curselection_func()

        # Return explicit absence when no row is selected.
        if not selected:
            return None
        return selected[0]

    def _on_step_selection_changed(self, _event: tk.Event[tk.Widget]) -> None:
        """Handles listbox selection changes.

        Args:
            _event: Tkinter event payload (unused).

        Returns:
            None.

        Raises:
            None.
        """
        # Refresh button states whenever selection changes.
        self._update_step_buttons_state()

    def _update_step_buttons_state(self) -> None:
        """Enables/disables workflow action buttons according to selection.

        Returns:
            None.

        Raises:
            tk.TclError: If Tkinter button state updates fail.
        """
        # Compute selected index and total count.
        selected_index = self.get_selected_step_index()
        total_steps = len(self._workflow_items)

        # Edit/Delete require a selected row.
        self._btn_edit_step.config(
            state=tk.NORMAL if selected_index is not None else tk.DISABLED,
        )
        self._btn_delete_step.config(
            state=tk.NORMAL if selected_index is not None else tk.DISABLED,
        )

        # Move up/down depends on index position.
        can_move_up = selected_index is not None and selected_index > 0
        can_move_down = selected_index is not None and selected_index < total_steps - 1
        self._btn_move_up.config(state=tk.NORMAL if can_move_up else tk.DISABLED)
        self._btn_move_down.config(state=tk.NORMAL if can_move_down else tk.DISABLED)

    def _notify_add_step(self) -> None:
        """Validates current instruction form then emits add callback.

        Returns:
            None.

        Raises:
            None.
        """
        # Resolve selected step type from displayed label.
        selected_label = self._var_step_type.get()
        step_type = self.ADD_OPTIONS.get(selected_label)

        # Guard against missing type selection.
        if step_type is None:
            self._show_error("Veuillez sélectionner un type d'étape avant d'ajouter.")
            return

        # Collect and validate dynamic form value.
        is_valid, step_value = self._collect_instruction_value(step_type)
        if not is_valid:
            return

        # Notify parent only when callback exists.
        if self._on_add_step:
            self._on_add_step(step_type, step_value)

    def _notify_edit_step(self) -> None:
        """Triggers the edit-step callback if registered.

        Returns:
            None.

        Raises:
            None.
        """
        # Delegate edit action to parent controller.
        if self._on_edit_step:
            self._on_edit_step()

    def _notify_delete_step(self) -> None:
        """Triggers the delete-step callback if registered.

        Returns:
            None.

        Raises:
            None.
        """
        # Delegate delete action to parent controller.
        if self._on_delete_step:
            self._on_delete_step()

    def _notify_move_up(self) -> None:
        """Triggers the move-up callback if registered.

        Returns:
            None.

        Raises:
            None.
        """
        # Delegate upward reordering to parent controller.
        if self._on_move_up:
            self._on_move_up()

    def _notify_move_down(self) -> None:
        """Triggers the move-down callback if registered.

        Returns:
            None.

        Raises:
            None.
        """
        # Delegate downward reordering to parent controller.
        if self._on_move_down:
            self._on_move_down()

    def _notify_clear_all(self) -> None:
        """Asks user confirmation then clears all workflow steps.

        Returns:
            None.

        Raises:
            tk.TclError: If confirmation dialog fails to open.
        """
        # Avoid unnecessary prompt when list is empty.
        if not self._workflow_items:
            return

        # Confirm destructive action with the user.
        should_clear = messagebox.askyesno(
            "Effacer",
            "Voulez-vous supprimer toutes les étapes du workflow ?",
        )
        if not should_clear:
            return

        # Delegate clear action if callback exists.
        if self._on_clear_all:
            self._on_clear_all()

    def _on_instruction_type_changed(self, _event: tk.Event[tk.Widget]) -> None:
        """Re-renders instruction form after type selection changes.

        Args:
            _event: Tkinter event payload (unused).

        Returns:
            None.

        Raises:
            None.
        """
        # Keep form fields aligned with selected step type.
        self._render_instruction_form()

    def _render_instruction_form(self) -> None:
        """Renders dynamic instruction inputs for selected step type.

        Returns:
            None.

        Raises:
            tk.TclError: If dynamic widget creation fails.
        """
        # Reset previous dynamic controls.
        self._clear_instruction_form()

        # Resolve internal step type from selected label.
        step_type = self._get_selected_step_type()
        if step_type is None:
            self._render_instruction_placeholder()
            return

        # Ensure second column can expand for entry widgets.
        self._instruction_form_frame.columnconfigure(1, weight=1)

        # Dispatch renderer for selected type.
        renderer = self._instruction_renderers().get(step_type)
        if renderer is None:
            self._render_instruction_placeholder()
            return
        renderer()

    def _clear_instruction_form(self) -> None:
        """Destroys current dynamic form widgets and resets bound vars.

        Returns:
            None.

        Raises:
            tk.TclError: If child widget destruction fails.
        """
        # Remove all current dynamic form controls.
        for child in self._instruction_form_frame.winfo_children():
            child.destroy()

        # Reset variable mapping to an empty state.
        self._instruction_form_vars = {}

    def _get_selected_step_type(self) -> Optional[str]:
        """Resolves the currently selected user label to step type token.

        Returns:
            Optional[str]: Internal step type identifier or ``None``.

        Raises:
            None.
        """
        # Translate combobox label to internal model token.
        return self.ADD_OPTIONS.get(self._var_step_type.get())

    def _render_instruction_placeholder(self) -> None:
        """Renders placeholder text when no step type is selected.

        Returns:
            None.

        Raises:
            tk.TclError: If label creation fails.
        """
        # Guide user before any type selection.
        ttk.Label(
            self._instruction_form_frame,
            text="Sélectionnez un type d'étape pour afficher ses paramètres.",
        ).grid(row=0, column=0, sticky="w")

    def _instruction_renderers(self) -> dict[str, Callable[[], None]]:
        """Returns mapping from step type to dedicated form renderer.

        Returns:
            dict[str, Callable[[], None]]: Renderer dispatch table.

        Raises:
            None.
        """
        # Keep renderer dispatch centralized and explicit.
        return {
            "open_url": self._render_open_url_form,
            "wait_seconds": self._render_wait_seconds_form,
            "refresh_page": self._render_refresh_page_form,
            "download_image": self._render_download_image_form,
            "check_if_image_here": self._render_check_image_form,
            "click_element": self._render_click_element_form,
        }

    def _render_open_url_form(self) -> None:
        """Renders inputs for the ``open_url`` step type.

        Returns:
            None.

        Raises:
            tk.TclError: If label or entry creation fails.
        """
        # Build one URL entry field.
        form = self._instruction_form_frame
        ttk.Label(form, text="URL:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )

        # Store bound variable for value collection.
        url_var = tk.StringVar()
        ttk.Entry(form, textvariable=url_var).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )
        self._instruction_form_vars = {"url": url_var}

    def _render_wait_seconds_form(self) -> None:
        """Renders inputs for the ``wait_seconds`` step type.

        Returns:
            None.

        Raises:
            tk.TclError: If combobox/entry creation fails.
        """
        # Build numeric duration entry.
        form = self._instruction_form_frame
        ttk.Label(form, text="Durée:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        amount_var = tk.StringVar(value="")
        ttk.Entry(form, textvariable=amount_var, width=20).grid(
            row=0,
            column=1,
            sticky="w",
            pady=(0, 8),
        )

        # Build unit selector from known mapping keys.
        ttk.Label(form, text="Unité:").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        unit_var = tk.StringVar(value="seconde")
        ttk.Combobox(
            form,
            textvariable=unit_var,
            values=list(self.WAIT_UNIT_MAP.keys()),
            state="readonly",
            width=18,
        ).grid(row=1, column=1, sticky="w", pady=(0, 8))
        self._instruction_form_vars = {"amount": amount_var, "unit": unit_var}

    def _render_refresh_page_form(self) -> None:
        """Renders inputs for the ``refresh_page`` step type.

        Returns:
            None.

        Raises:
            tk.TclError: If label or checkbox creation fails.
        """
        # Display explanatory text for this boolean option.
        form = self._instruction_form_frame
        ttk.Label(
            form,
            text="Cette étape rafraîchira la page active.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Build checkbox and store bound variable.
        clear_cache_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            form,
            text="Vider le cache avant rafraîchissement",
            variable=clear_cache_var,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._instruction_form_vars = {"clear_cache": clear_cache_var}

    def _render_download_image_form(self) -> None:
        """Renders inputs for the ``download_image`` step type.

        Returns:
            None.

        Raises:
            tk.TclError: If one of the controls cannot be created.
        """
        # Prepare all bound variables for this form.
        form = self._instruction_form_frame
        mode_var, min_w, min_h, max_w, max_h = self._create_download_form_vars()

        # Render mode label and dedicated control groups.
        ttk.Label(form, text="Mode de téléchargement:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        self._grid_download_mode_controls(form, mode_var)
        self._grid_download_dimension_controls(form, min_w, min_h, max_w, max_h)

        # Store values for collector phase.
        self._instruction_form_vars = {
            "mode": mode_var,
            "min_width": min_w,
            "min_height": min_h,
            "max_width": max_w,
            "max_height": max_h,
        }

    def _create_download_form_vars(
        self,
    ) -> tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar]:
        """Creates Tk variables used by the download-image form.

        Returns:
            tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar,
            tk.StringVar]: ``(mode, min_w, min_h, max_w, max_h)`` variables.

        Raises:
            tk.TclError: If Tk variable initialization fails.
        """
        # Initialize default values for all download fields.
        return (
            tk.StringVar(value="largest"),
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
        )

    def _grid_download_mode_controls(
        self,
        form: ttk.Frame,
        mode_var: tk.StringVar,
    ) -> None:
        """Renders radio controls for image download mode.

        Args:
            form: Parent dynamic form frame.
            mode_var: Bound Tk variable for selected mode.

        Returns:
            None.

        Raises:
            tk.TclError: If radio button creation fails.
        """
        # Offer three mutually exclusive mode choices.
        ttk.Radiobutton(
            form,
            text="La plus grande image",
            variable=mode_var,
            value="largest",
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        ttk.Radiobutton(
            form,
            text="La première image",
            variable=mode_var,
            value="first",
        ).grid(row=1, column=1, sticky="w", pady=(0, 4))
        ttk.Radiobutton(
            form,
            text="Toutes les images",
            variable=mode_var,
            value="all",
        ).grid(row=2, column=1, sticky="w", pady=(0, 8))

    def _grid_download_dimension_controls(
        self,
        form: ttk.Frame,
        min_w: tk.StringVar,
        min_h: tk.StringVar,
        max_w: tk.StringVar,
        max_h: tk.StringVar,
    ) -> None:
        """Renders width/height limit controls for image filtering.

        Args:
            form: Parent dynamic form frame.
            min_w: Minimum width variable.
            min_h: Minimum height variable.
            max_w: Maximum width variable.
            max_h: Maximum height variable.

        Returns:
            None.

        Raises:
            tk.TclError: If labels or entries fail to render.
        """
        # Render minimum dimension inputs.
        ttk.Label(form, text="Largeur min (W):").grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=min_w, width=16).grid(
            row=3,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(form, text="Hauteur min (H):").grid(
            row=4,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=min_h, width=16).grid(
            row=4,
            column=1,
            sticky="w",
            pady=(0, 8),
        )

        # Render maximum dimension inputs.
        ttk.Label(form, text="Largeur max (W):").grid(
            row=5,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=max_w, width=16).grid(
            row=5,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(form, text="Hauteur max (H):").grid(
            row=6,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=max_h, width=16).grid(
            row=6,
            column=1,
            sticky="w",
            pady=(0, 8),
        )

    def _render_check_image_form(self) -> None:
        """Renders inputs for the ``check_if_image_here`` step type.

        Returns:
            None.

        Raises:
            tk.TclError: If labels or entries fail to render.
        """
        # Prepare all bound boundary variables.
        form = self._instruction_form_frame
        w1, w2, h1, h2 = self._create_check_image_vars()

        # Render labels, entries, and condition hint.
        self._grid_check_image_labels(form)
        self._grid_check_image_entries(form, w1, w2, h1, h2)
        ttk.Label(
            form,
            text="Condition: W1 < X < W2 et H1 < Y < H2",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Keep bound values for collector phase.
        self._instruction_form_vars = {"w1": w1, "w2": w2, "h1": h1, "h2": h2}

    def _create_check_image_vars(
        self,
    ) -> tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar]:
        """Creates Tk variables for image-boundary checks.

        Returns:
            tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar]:
            ``(w1, w2, h1, h2)`` variables.

        Raises:
            tk.TclError: If Tk variable creation fails.
        """
        # Initialize all bounds to zero.
        return (
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
        )

    def _grid_check_image_labels(self, form: ttk.Frame) -> None:
        """Renders labels for image-boundary inputs.

        Args:
            form: Parent dynamic form frame.

        Returns:
            None.

        Raises:
            tk.TclError: If label creation fails.
        """
        # Render coordinate labels in logical order.
        ttk.Label(form, text="W1:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(form, text="W2:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(form, text="H1:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(form, text="H2:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

    def _grid_check_image_entries(
        self,
        form: ttk.Frame,
        w1: tk.StringVar,
        w2: tk.StringVar,
        h1: tk.StringVar,
        h2: tk.StringVar,
    ) -> None:
        """Renders entries for image-boundary inputs.

        Args:
            form: Parent dynamic form frame.
            w1: Lower width bound variable.
            w2: Upper width bound variable.
            h1: Lower height bound variable.
            h2: Upper height bound variable.

        Returns:
            None.

        Raises:
            tk.TclError: If entry creation fails.
        """
        # Bind each boundary to a dedicated entry widget.
        ttk.Entry(form, textvariable=w1, width=16).grid(
            row=0,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=w2, width=16).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=h1, width=16).grid(
            row=2,
            column=1,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=h2, width=16).grid(
            row=3,
            column=1,
            sticky="w",
            pady=(0, 8),
        )

    def _render_click_element_form(self) -> None:
        """Renders inputs for the ``click_element`` step type.

        Returns:
            None.

        Raises:
            tk.TclError: If labels, entries, or checkboxes cannot be created.
        """
        # Create all Tk variables required by click settings.
        form = self._instruction_form_frame
        selector, normal, forced, js_direct, verify = self._create_click_element_vars()

        # Render selector input and click-mode checkboxes.
        ttk.Label(form, text="Sélecteur CSS:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 8),
        )
        ttk.Entry(form, textvariable=selector).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )
        self._grid_click_mode_controls(form, normal, forced, js_direct, verify)

        # Save variables for collector phase.
        self._instruction_form_vars = {
            "selector": selector,
            "normal": normal,
            "forced": forced,
            "js_direct": js_direct,
            "verify_present": verify,
        }

    def _create_click_element_vars(
        self,
    ) -> tuple[tk.StringVar, tk.BooleanVar, tk.BooleanVar, tk.BooleanVar, tk.BooleanVar]:
        """Creates Tk variables used by click-element form controls.

        Returns:
            tuple[tk.StringVar, tk.BooleanVar, tk.BooleanVar, tk.BooleanVar,
            tk.BooleanVar]: ``(selector, normal, forced, js_direct, verify)``.

        Raises:
            tk.TclError: If Tk variable creation fails.
        """
        # Initialize selector and mode flags with safe defaults.
        return (
            tk.StringVar(value=""),
            tk.BooleanVar(value=True),
            tk.BooleanVar(value=False),
            tk.BooleanVar(value=False),
            tk.BooleanVar(value=False),
        )

    def _grid_click_mode_controls(
        self,
        form: ttk.Frame,
        normal: tk.BooleanVar,
        forced: tk.BooleanVar,
        js_direct: tk.BooleanVar,
        verify: tk.BooleanVar,
    ) -> None:
        """Renders checkboxes for click mode flags.

        Args:
            form: Parent dynamic form frame.
            normal: Standard click mode flag.
            forced: Forced click mode flag.
            js_direct: JavaScript direct-click mode flag.
            verify: Presence-check flag before clicking.

        Returns:
            None.

        Raises:
            tk.TclError: If checkbox creation fails.
        """
        # Expose each click strategy as a separate checkbox.
        ttk.Checkbutton(
            form,
            text="Normal",
            variable=normal,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Checkbutton(
            form,
            text="Forced",
            variable=forced,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Checkbutton(
            form,
            text="JS Direct",
            variable=js_direct,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Checkbutton(
            form,
            text="Vérifier présent du bouton",
            variable=verify,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))

    def _collect_instruction_value(self, step_type: str) -> tuple[bool, Any]:
        """Collects and validates dynamic form values for the given step type.

        Args:
            step_type: Internal step type token.

        Returns:
            tuple[bool, Any]: ``(is_valid, value)`` where ``value`` is normalized
            payload for downstream step creation.

        Raises:
            None.
        """
        # Select collector from centralized dispatch map.
        collector = self._value_collectors().get(step_type)
        if collector is None:
            self._show_error("Type d'étape invalide.")
            return False, None

        # Run collector and return validation result.
        return collector()

    def _value_collectors(self) -> dict[str, Callable[[], tuple[bool, Any]]]:
        """Returns mapping from step type to value collector function.

        Returns:
            dict[str, Callable[[], tuple[bool, Any]]]: Collector dispatch map.

        Raises:
            None.
        """
        # Keep collector dispatch explicit and local.
        return {
            "open_url": self._collect_open_url_value,
            "wait_seconds": self._collect_wait_seconds_value,
            "refresh_page": self._collect_refresh_page_value,
            "download_image": self._collect_download_image_value,
            "check_if_image_here": self._collect_check_image_value,
            "click_element": self._collect_click_element_value,
        }

    def _collect_open_url_value(self) -> tuple[bool, Any]:
        """Collects and validates value for the ``open_url`` step.

        Returns:
            tuple[bool, Any]: Validity flag and URL string payload.

        Raises:
            None.
        """
        # Read URL field and trim extra spaces.
        url_var = cast(tk.StringVar, self._instruction_form_vars.get("url"))
        value = url_var.get().strip()

        # Enforce required URL value.
        if not value:
            self._show_error("La valeur URL est obligatoire.")
            return False, None
        return True, value

    def _collect_wait_seconds_value(self) -> tuple[bool, Any]:
        """Collects and validates value for the ``wait_seconds`` step.

        Returns:
            tuple[bool, Any]: Validity flag and normalized wait payload.

        Raises:
            None.
        """
        # Read duration and selected display unit.
        amount_var = cast(tk.StringVar, self._instruction_form_vars.get("amount"))
        unit_var = cast(tk.StringVar, self._instruction_form_vars.get("unit"))
        amount_raw = amount_var.get().strip()

        # Validate duration is a strictly positive integer.
        if not amount_raw:
            self._show_error("La durée est obligatoire.")
            return False, None
        if not amount_raw.isdigit() or int(amount_raw) <= 0:
            self._show_error("La durée doit être un entier positif.")
            return False, None

        # Convert localized unit label to backend token.
        unit_token = self.WAIT_UNIT_MAP.get(unit_var.get(), "seconds")
        return True, {"amount": int(amount_raw), "unit": unit_token}

    def _collect_refresh_page_value(self) -> tuple[bool, Any]:
        """Collects value for the ``refresh_page`` step.

        Returns:
            tuple[bool, Any]: Always valid; returns a boolean payload.

        Raises:
            None.
        """
        # Read single boolean option from checkbox.
        clear_cache_var = cast(
            tk.BooleanVar,
            self._instruction_form_vars.get("clear_cache"),
        )
        return True, clear_cache_var.get()

    def _collect_download_image_value(self) -> tuple[bool, Any]:
        """Collects and validates value for the ``download_image`` step.

        Returns:
            tuple[bool, Any]: Validity flag and normalized download payload.

        Raises:
            None.
        """
        # Read all raw fields from bound variables.
        mode_var = cast(tk.StringVar, self._instruction_form_vars.get("mode"))
        min_w = cast(tk.StringVar, self._instruction_form_vars.get("min_width"))
        min_h = cast(tk.StringVar, self._instruction_form_vars.get("min_height"))
        max_w = cast(tk.StringVar, self._instruction_form_vars.get("max_width"))
        max_h = cast(tk.StringVar, self._instruction_form_vars.get("max_height"))

        # Parse all boundaries and stop if one is invalid.
        parsed = self._parse_download_limits(
            min_w.get(),
            min_h.get(),
            max_w.get(),
            max_h.get(),
        )
        if parsed is None:
            return False, None

        # Build normalized payload for presenter/model layer.
        min_width, min_height, max_width, max_height = parsed
        return True, self._build_download_value(
            mode_var.get(),
            min_width,
            min_height,
            max_width,
            max_height,
        )

    def _parse_download_limits(
        self,
        min_w_raw: str,
        min_h_raw: str,
        max_w_raw: str,
        max_h_raw: str,
    ) -> Optional[tuple[int, int, int, int]]:
        """Parses and validates numeric limits for ``download_image``.

        Args:
            min_w_raw: Raw minimum width text.
            min_h_raw: Raw minimum height text.
            max_w_raw: Raw maximum width text.
            max_h_raw: Raw maximum height text.

        Returns:
            Optional[tuple[int, int, int, int]]: Parsed limits or ``None`` when
            at least one value is invalid.

        Raises:
            None.
        """
        # Parse each field independently to show specific errors.
        min_width = self._parse_non_negative_int(min_w_raw, "La largeur minimale")
        if min_width is None:
            return None
        min_height = self._parse_non_negative_int(min_h_raw, "La hauteur minimale")
        if min_height is None:
            return None
        max_width = self._parse_non_negative_int(max_w_raw, "La largeur maximale")
        if max_width is None:
            return None
        max_height = self._parse_non_negative_int(max_h_raw, "La hauteur maximale")
        if max_height is None:
            return None
        return min_width, min_height, max_width, max_height

    def _build_download_value(
        self,
        mode: str,
        min_width: int,
        min_height: int,
        max_width: int,
        max_height: int,
    ) -> dict[str, Any]:
        """Builds normalized payload for ``download_image``.

        Args:
            mode: Download strategy token.
            min_width: Minimum width filter.
            min_height: Minimum height filter.
            max_width: Maximum width filter.
            max_height: Maximum height filter.

        Returns:
            dict[str, Any]: Normalized payload dictionary.

        Raises:
            None.
        """
        # Keep output schema explicit for readability and testing.
        return {
            "mode": mode,
            "min_width": min_width,
            "min_height": min_height,
            "max_width": max_width,
            "max_height": max_height,
        }

    def _collect_check_image_value(self) -> tuple[bool, Any]:
        """Collects and validates value for ``check_if_image_here``.

        Returns:
            tuple[bool, Any]: Validity flag and bounds payload.

        Raises:
            None.
        """
        # Read raw boundary values from bound variables.
        w1_var = cast(tk.StringVar, self._instruction_form_vars.get("w1"))
        w2_var = cast(tk.StringVar, self._instruction_form_vars.get("w2"))
        h1_var = cast(tk.StringVar, self._instruction_form_vars.get("h1"))
        h2_var = cast(tk.StringVar, self._instruction_form_vars.get("h2"))

        # Parse and validate ordering constraints.
        bounds = self._parse_check_image_bounds(
            w1_var.get(),
            w2_var.get(),
            h1_var.get(),
            h2_var.get(),
        )
        if bounds is None:
            return False, None

        # Return normalized boundary payload.
        w1, w2, h1, h2 = bounds
        return True, {"w1": w1, "w2": w2, "h1": h1, "h2": h2}

    def _parse_check_image_bounds(
        self,
        w1_raw: str,
        w2_raw: str,
        h1_raw: str,
        h2_raw: str,
    ) -> Optional[tuple[int, int, int, int]]:
        """Parses and validates integer bounds for image-area checks.

        Args:
            w1_raw: Raw lower width bound.
            w2_raw: Raw upper width bound.
            h1_raw: Raw lower height bound.
            h2_raw: Raw upper height bound.

        Returns:
            Optional[tuple[int, int, int, int]]: Parsed bounds when valid,
            otherwise ``None``.

        Raises:
            None.
        """
        # Parse each bound and stop on first invalid value.
        w1 = self._parse_int(w1_raw, "W1")
        if w1 is None:
            return None
        w2 = self._parse_int(w2_raw, "W2")
        if w2 is None:
            return None
        h1 = self._parse_int(h1_raw, "H1")
        if h1 is None:
            return None
        h2 = self._parse_int(h2_raw, "H2")
        if h2 is None:
            return None

        # Enforce strictly increasing bounds per axis.
        if w1 >= w2:
            self._show_error("W1 doit être strictement inférieur à W2.")
            return None
        if h1 >= h2:
            self._show_error("H1 doit être strictement inférieur à H2.")
            return None
        return w1, w2, h1, h2

    def _collect_click_element_value(self) -> tuple[bool, Any]:
        """Collects and validates value for ``click_element``.

        Returns:
            tuple[bool, Any]: Validity flag and click configuration payload.

        Raises:
            None.
        """
        # Read variables bound to selector and mode checkboxes.
        selector_var = cast(tk.StringVar, self._instruction_form_vars.get("selector"))
        normal_var = cast(tk.BooleanVar, self._instruction_form_vars.get("normal"))
        forced_var = cast(tk.BooleanVar, self._instruction_form_vars.get("forced"))
        js_direct_var = cast(tk.BooleanVar, self._instruction_form_vars.get("js_direct"))
        verify_var = cast(
            tk.BooleanVar,
            self._instruction_form_vars.get("verify_present"),
        )

        # Validate required selector value.
        selector = selector_var.get().strip()
        if not selector:
            self._show_error("Le sélecteur CSS est obligatoire.")
            return False, None

        # Validate at least one click mode enabled.
        normal, forced, js_direct = (
            normal_var.get(),
            forced_var.get(),
            js_direct_var.get(),
        )
        if not (normal or forced or js_direct):
            self._show_error(
                "Sélectionnez au moins un mode de clic (Normal, Forced ou JS Direct).",
            )
            return False, None

        # Build and return normalized click payload.
        return True, self._build_click_value(
            selector,
            normal,
            forced,
            js_direct,
            verify_var.get(),
        )

    def _build_click_value(
        self,
        selector: str,
        normal: bool,
        forced: bool,
        js_direct: bool,
        verify_present: bool,
    ) -> dict[str, Any]:
        """Builds normalized payload for ``click_element``.

        Args:
            selector: CSS selector to click.
            normal: Normal click mode flag.
            forced: Forced click mode flag.
            js_direct: JavaScript direct-click mode flag.
            verify_present: Presence check flag before click attempt.

        Returns:
            dict[str, Any]: Normalized click payload dictionary.

        Raises:
            None.
        """
        # Return explicit schema consumed by the presenter/service layer.
        return {
            "selector": selector,
            "normal": normal,
            "forced": forced,
            "js_direct": js_direct,
            "verify_present": verify_present,
        }

    def _parse_non_negative_int(self, raw: str, label: str) -> Optional[int]:
        """Parses a non-negative integer and shows user error on failure.

        Args:
            raw: Raw input text to parse.
            label: Human-readable field label used in error messages.

        Returns:
            Optional[int]: Parsed integer or ``None`` when invalid.

        Raises:
            None.

        Example:
            value = self._parse_non_negative_int("12", "Width")
            if value is not None:
                print(value)
        """
        # Normalize whitespace before validation checks.
        value = raw.strip()
        if not value:
            self._show_error(f"{label} est obligatoire.")
            return None
        if not value.isdigit():
            self._show_error(f"{label} doit être un entier >= 0.")
            return None

        # Convert validated string to integer.
        return int(value)

    def _parse_int(self, raw: str, label: str) -> Optional[int]:
        """Parses a signed integer and shows user error on failure.

        Args:
            raw: Raw input text to parse.
            label: Human-readable field label used in error messages.

        Returns:
            Optional[int]: Parsed integer or ``None`` when invalid.

        Raises:
            None.

        Example:
            offset = self._parse_int("-3", "Offset")
            if offset is not None:
                print(offset)
        """
        # Normalize whitespace before validation checks.
        value = raw.strip()
        if not value:
            self._show_error(f"{label} est obligatoire.")
            return None

        # Validate negative and non-negative numeric forms.
        if value.startswith("-"):
            if not value[1:].isdigit():
                self._show_error(f"{label} doit être un entier.")
                return None
        elif not value.isdigit():
            self._show_error(f"{label} doit être un entier.")
            return None

        # Convert validated string to integer.
        return int(value)

    def _show_error(self, message: str) -> None:
        """Displays a standardized error dialog.

        Args:
            message: Error message text shown to the user.

        Returns:
            None.

        Raises:
            tk.TclError: If message box cannot be displayed.
        """
        # Keep all error messages visually consistent.
        messagebox.showerror("Erreur", message)
