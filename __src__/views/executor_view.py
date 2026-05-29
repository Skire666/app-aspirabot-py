"""Tkinter view for the executor panel.

Passive widget tree bound to ``ExecutorViewModel``.  All widget state is
driven by ViewModel Vars; all user actions are forwarded to the ViewModel
action methods.  No business logic, no service calls.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from view_models.executor_view_model import ExecutorViewModel, ScenarioItem
from views.components.column_combobox import ColumnCombobox
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ExecutorView(ttk.Frame):
    """Panel that lets the user configure and launch a scraping session.

    Sections:
        1. Scenario selection (ColumnCombobox + Refresh + Edit buttons).
        2. Available profiles (Listbox + CRUD buttons + saved-date label).
        3. Launch profile configuration (export folder, URL source, thresholds).
        4. Launch trigger (verification label + launch button).

    The view is purely passive: every widget is bound to a ``ExecutorViewModel``
    Var or reacts to a version-trigger Var via ``trace_add``.
    """

    def __init__(self, parent: tk.Widget, vm: ExecutorViewModel) -> None:
        """Build widget structure and bind to the ViewModel.

        Args:
            parent: Parent Tkinter container.
            vm: The ViewModel that owns all UI state for this panel.
        """
        super().__init__(parent)
        self._vm = vm

        # Local rendering caches — refreshed from VM list data on version changes.
        self._profile_items: list = []
        self._step_items: list = []

        # Cooldown guard for refresh button.
        self._refresh_cooldown: bool = False

        self._create_widgets()
        self._bind_vm_vars()
        # Register View as the error-dialog provider for the Presenter.
        vm.bind_show_error(self.show_error)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build all four sections in order."""
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._create_scenario_section(outer)
        self._create_profiles_section(outer)
        self._create_profile_config_section(outer)
        self._create_launch_section(outer)

    def _create_scenario_section(self, parent: tk.Widget) -> None:
        """Build the scenario selection section."""
        frame = HorizontalLineFrame(parent, text="Liste des scénarios")
        frame.pack(fill=tk.X, pady=(0, 4))

        self._combo_scenarios = ColumnCombobox(frame, width=60)
        self._combo_scenarios.add_column("scenario_name", lambda m: m.scenario_name, width=220)
        self._combo_scenarios.add_column("scenario_desc", lambda m: m.scenario_desc, width=260)
        self._combo_scenarios.add_column("id_file", lambda m: m.id_file, width=90)
        self._combo_scenarios.set_display_column("scenario_name")
        self._combo_scenarios.bind("<<ComboboxSelected>>", self._on_combo_scenario_changed)
        self._combo_scenarios.pack(side=tk.LEFT, padx=(5, 8), pady=(0, 6))

        self._btn_edit = ttk.Button(frame, text="Modifier", command=self._on_edit_clicked)
        self._btn_edit.pack(side=tk.RIGHT, padx=(4, 5), pady=(0, 6))

        self._btn_refresh = ttk.Button(frame, text="Rafraîchir", command=self._on_refresh_clicked)
        self._btn_refresh.pack(side=tk.RIGHT, padx=(0, 4), pady=(0, 6))

    def _create_profiles_section(self, parent: tk.Widget) -> None:
        """Build the available-profiles section."""
        frame = HorizontalLineFrame(parent, text="Profils disponibles")
        frame.pack(fill=tk.X, pady=(0, 4))

        self._listbox_profiles = tk.Listbox(frame, height=5, selectmode=tk.SINGLE, exportselection=False)
        self._listbox_profiles.pack(fill=tk.X, padx=5, pady=(0, 4))
        self._listbox_profiles.bind("<<ListboxSelect>>", self._on_listbox_profile_selected)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, padx=5, pady=(0, 6))

        self._btn_new = ttk.Button(btn_row, text="Nouveau", command=self._on_new_clicked)
        self._btn_new.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_rename = ttk.Button(btn_row, text="Renommer", command=self._on_rename_clicked)
        self._btn_rename.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_delete = ttk.Button(btn_row, text="Supprimer", command=self._on_delete_clicked)
        self._btn_delete.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_save = ttk.Button(btn_row, text="Sauvegarder", command=lambda: self._vm.save_profile())
        self._btn_save.pack(side=tk.LEFT, padx=(0, 8))

        self._lbl_saved = ttk.Label(btn_row, textvariable=self._vm.saved_date_var)
        self._lbl_saved.pack(side=tk.LEFT)

    def _create_profile_config_section(self, parent: tk.Widget) -> None:
        """Build the launch-profile configuration section."""
        self._frame_profile_cfg = HorizontalLineFrame(parent, text="Profil de lancement")
        self._frame_profile_cfg.pack(fill=tk.X, pady=(0, 4))
        grid = ttk.Frame(self._frame_profile_cfg)
        grid.pack(fill=tk.X, padx=5, pady=(0, 6))
        self._cfg_grid = grid
        self._create_cfg_row0(grid)
        self._create_cfg_row1(grid)
        self._create_cfg_row2(grid)
        self._create_cfg_row3(grid)
        self._create_cfg_row4(grid)
        self._create_cfg_row5(grid)
        self._create_cfg_row6(grid)

    def _create_cfg_row0(self, grid: tk.Widget) -> None:
        """Row 0 — usage statistics (last used date, launch count)."""
        ttk.Label(grid, text="Dernière utilisation :").grid(row=0, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        ttk.Label(grid, textvariable=self._vm.used_date_var).grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=2)
        ttk.Label(grid, text="Lancements :").grid(row=0, column=2, sticky=tk.W, padx=(0, 4), pady=2)
        ttk.Label(grid, textvariable=self._vm.launch_count_var).grid(row=0, column=3, sticky=tk.W, pady=2)

    def _create_cfg_row1(self, grid: tk.Widget) -> None:
        """Row 1 — export folder path, browse button, open-folder button."""
        ttk.Label(grid, text="Dossier d'export :").grid(row=1, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._vm.export_folder_var.trace_add("write", lambda *_: self._vm.form_changed())
        entry = ttk.Entry(grid, textvariable=self._vm.export_folder_var, width=50)
        entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=(0, 4), pady=2)
        ttk.Button(grid, text="Parcourir", command=self._browse_export_folder).grid(
            row=1, column=3, padx=(0, 4), pady=2
        )
        ttk.Button(grid, text="Ouvrir dossier", command=lambda: self._vm.open_export_folder()).grid(
            row=1, column=4, pady=2
        )

    def _create_cfg_row2(self, grid: tk.Widget) -> None:
        """Row 2 — URL source type combobox and folder/json path entry."""
        ttk.Label(grid, text="Source d'URL :").grid(row=2, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        source_choices = [
            ("Liste manuelle", UrlSourceTypeEnum.E_MANUAL.value),
            ("Dossier avec URL", UrlSourceTypeEnum.E_FOLDER.value),
            ("Dossier avec JSON", UrlSourceTypeEnum.E_JSON.value),
        ]
        self._source_choices = source_choices
        display_values = [label for label, _ in source_choices]
        self._combo_source = ttk.Combobox(grid, values=display_values, state="readonly", width=22)
        self._combo_source.grid(row=2, column=1, sticky=tk.W, pady=2)
        self._combo_source.bind("<<ComboboxSelected>>", self._on_source_type_changed)

        self._vm.url_source_path_var.trace_add("write", lambda *_: self._vm.form_changed())
        self._entry_source_path = ttk.Entry(grid, textvariable=self._vm.url_source_path_var, width=40)
        self._entry_source_path.grid(row=2, column=2, columnspan=2, sticky=tk.EW, padx=(8, 4), pady=2)
        self._btn_browse_source = ttk.Button(grid, text="Parcourir", command=self._browse_source_folder)
        self._btn_browse_source.grid(row=2, column=4, pady=2)

    def _create_cfg_row3(self, grid: tk.Widget) -> None:
        """Row 3 — URL preview (scrollable, editable only in manual mode)."""
        ttk.Label(grid, text="Aperçu URLs :").grid(row=3, column=0, sticky=tk.NW, padx=(0, 4), pady=2)
        preview_frame = ttk.Frame(grid)
        preview_frame.grid(row=3, column=1, columnspan=4, sticky=tk.EW, pady=2)
        self._txt_url_preview = tk.Text(preview_frame, height=7, width=70, wrap=tk.NONE)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_preview.yview)
        self._txt_url_preview.configure(yscrollcommand=scrollbar.set)
        self._txt_url_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_preview.bind("<<Modified>>", self._on_url_text_modified)

    def _create_cfg_row4(self, grid: tk.Widget) -> None:
        """Row 4 — sort-order radio buttons (active for folder/json only)."""
        ttk.Label(grid, text="Ordre de lecture :").grid(row=4, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        rb_frame = ttk.Frame(grid)
        rb_frame.grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=2)
        self._rb_recent = ttk.Radiobutton(
            rb_frame,
            text="Lire récemment modifié",
            variable=self._vm.url_sort_order_var,
            value=UrlSortOrderEnum.E_MTIME_DESC.value,
            command=lambda: self._vm.form_changed(),
        )
        self._rb_recent.pack(side=tk.LEFT, padx=(0, 12))
        self._rb_oldest = ttk.Radiobutton(
            rb_frame,
            text="Lire les plus anciens",
            variable=self._vm.url_sort_order_var,
            value=UrlSortOrderEnum.E_MTIME_ASC.value,
            command=lambda: self._vm.form_changed(),
        )
        self._rb_oldest.pack(side=tk.LEFT)
        self._rb_recent.state(["disabled"])
        self._rb_oldest.state(["disabled"])

    def _create_cfg_row5(self, grid: tk.Widget) -> None:
        """Row 5 — global error threshold."""
        ttk.Label(grid, text="Erreurs globales max. avant mise en pause d'urgence :").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, padx=(0, 4), pady=2
        )
        self._vm.global_threshold_var.trace_add("write", lambda *_: self._vm.form_changed())
        ttk.Entry(grid, textvariable=self._vm.global_threshold_var, width=12).grid(row=5, column=2, sticky=tk.W, pady=2)

    def _create_cfg_row6(self, grid: tk.Widget) -> None:
        """Row 6 — per-step error threshold with step selector."""
        ttk.Label(grid, text="Mise en pause d'urgence sur :").grid(row=6, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._combo_steps = ttk.Combobox(grid, state="readonly", width=38)
        self._combo_steps.grid(row=6, column=1, columnspan=2, sticky=tk.EW, padx=(0, 4), pady=2)
        self._combo_steps.bind("<<ComboboxSelected>>", self._on_step_selected)
        self._vm.step_threshold_var.trace_add("write", lambda *_: self._vm.form_changed())
        ttk.Entry(grid, textvariable=self._vm.step_threshold_var, width=12).grid(
            row=6, column=3, sticky=tk.W, padx=(0, 4), pady=2
        )
        ttk.Label(grid, text="erreurs").grid(row=6, column=4, sticky=tk.W, pady=2)

    def _create_launch_section(self, parent: tk.Widget) -> None:
        """Build the launch-trigger section."""
        frame = HorizontalLineFrame(parent, text="Lancer le scraping")
        frame.pack(fill=tk.X, pady=(0, 4))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=5, pady=(0, 6))

        ttk.Label(row, text="Vérification :").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(row, textvariable=self._vm.verification_message_var, foreground="red").pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        self._btn_launch = ttk.Button(row, text="Lancer le scraping", command=lambda: self._vm.launch())
        self._btn_launch.pack(side=tk.RIGHT, padx=(8, 0))

    # ------------------------------------------------------------------
    # ViewModel bindings (trace_add for non-Var widgets)
    # ------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace_add listeners for all non-Var widget bindings."""
        self._vm.scenarios_version_var.trace_add("write", self._sync_scenarios)
        self._vm.selected_scenario_id_var.trace_add("write", self._sync_scenario_selection)
        self._vm.profiles_version_var.trace_add("write", self._sync_profiles)
        self._vm.selected_profile_id_var.trace_add("write", self._sync_profile_selection)
        self._vm.steps_version_var.trace_add("write", self._sync_steps)
        self._vm.step_id_selected_var.trace_add("write", self._sync_step_selection)
        self._vm.url_preview_version_var.trace_add("write", self._sync_url_preview)
        self._vm.url_source_type_var.trace_add("write", self._sync_url_source_type)
        self._vm.is_profiles_list_enabled_var.trace_add("write", self._sync_profiles_list_enabled)
        self._vm.is_profile_section_enabled_var.trace_add("write", self._sync_profile_section_enabled)
        self._vm.is_edit_btn_enabled_var.trace_add("write", self._sync_edit_btn)
        self._vm.is_rename_btn_enabled_var.trace_add("write", self._sync_rename_btn)
        self._vm.is_delete_btn_enabled_var.trace_add("write", self._sync_delete_btn)
        self._vm.is_save_btn_enabled_var.trace_add("write", self._sync_save_btn)
        self._vm.is_path_entry_enabled_var.trace_add("write", self._sync_path_entry)
        self._vm.is_sort_order_enabled_var.trace_add("write", self._sync_sort_order)
        self._vm.is_preview_editable_var.trace_add("write", self._sync_preview_editable)

    # ------------------------------------------------------------------
    # Sync methods (called by trace_add)
    # ------------------------------------------------------------------

    def _sync_scenarios(self, *_: object) -> None:
        """Re-render the scenario combobox from the ViewModel list."""
        self._combo_scenarios.clear()
        self._combo_scenarios.add_items(self._vm.get_scenarios())

    def _sync_scenario_selection(self, *_: object) -> None:
        """Select the combobox entry matching selected_scenario_id_var."""
        target_id = self._vm.selected_scenario_id_var.get()
        for idx in range(self._combo_scenarios.size()):
            obj = self._combo_scenarios.get_object_at(idx)
            if obj and getattr(obj, "id_file", None) == target_id:
                self._combo_scenarios.current(idx)
                return

    def _sync_profiles(self, *_: object) -> None:
        """Re-render the profile listbox from the ViewModel list."""
        self._profile_items = self._vm.get_profiles()
        self._listbox_profiles.delete(0, tk.END)
        for item in self._profile_items:
            self._listbox_profiles.insert(tk.END, item.profile_name)

    def _sync_profile_selection(self, *_: object) -> None:
        """Select the listbox row matching selected_profile_id_var."""
        target_id = self._vm.selected_profile_id_var.get()
        for idx, item in enumerate(self._profile_items):
            if item.id_profile == target_id:
                self._listbox_profiles.selection_clear(0, tk.END)
                self._listbox_profiles.selection_set(idx)
                self._listbox_profiles.see(idx)
                return

    def _sync_steps(self, *_: object) -> None:
        """Re-render the emergency-stop combobox from the ViewModel step list."""
        self._step_items = self._vm.get_steps()
        self._combo_steps["values"] = [s.label for s in self._step_items]

    def _sync_step_selection(self, *_: object) -> None:
        """Select the step combobox entry matching step_id_selected_var."""
        target_id = self._vm.step_id_selected_var.get()
        for idx, s in enumerate(self._step_items):
            if s.step_id == target_id:
                self._combo_steps.current(idx)
                return
        self._combo_steps.set("")

    def _sync_url_preview(self, *_: object) -> None:
        """Update the URL preview Text widget from the ViewModel list."""
        text = "\n".join(self._vm.get_url_preview())
        self._set_url_preview_text(text, editable=False)

    def _sync_url_source_type(self, *_: object) -> None:
        """Select the URL-source combobox entry matching url_source_type_var."""
        target = self._vm.url_source_type_var.get()
        for idx, (_, value) in enumerate(self._source_choices):
            if value == target:
                self._combo_source.current(idx)
                return
        self._combo_source.set("")

    def _sync_profiles_list_enabled(self, *_: object) -> None:
        """Enable or disable the profile listbox and Nouveau button."""
        state = tk.NORMAL if self._vm.is_profiles_list_enabled_var.get() else tk.DISABLED
        self._listbox_profiles.configure(state=state)
        self._btn_new.configure(state=state)

    def _sync_profile_section_enabled(self, *_: object) -> None:
        """Enable or disable the entire profile-config grid."""
        import contextlib

        enabled = self._vm.is_profile_section_enabled_var.get()
        for child in self._cfg_grid.winfo_children():
            with contextlib.suppress(tk.TclError):
                if not enabled:
                    child.configure(state=tk.DISABLED)
                    continue
                if isinstance(child, ttk.Combobox):
                    child.configure(state="readonly")
                else:
                    child.configure(state=tk.NORMAL)
        if enabled:
            self._sync_url_source_type()
            self._sync_path_entry()
            self._sync_sort_order()
            self._sync_preview_editable()
        else:
            self._txt_url_preview.configure(state=tk.DISABLED)

    def _sync_edit_btn(self, *_: object) -> None:
        """Mirror is_edit_btn_enabled_var onto the Modifier button."""
        state = tk.NORMAL if self._vm.is_edit_btn_enabled_var.get() else tk.DISABLED
        self._btn_edit.configure(state=state)

    def _sync_rename_btn(self, *_: object) -> None:
        """Mirror is_rename_btn_enabled_var onto the Renommer button."""
        state = tk.NORMAL if self._vm.is_rename_btn_enabled_var.get() else tk.DISABLED
        self._btn_rename.configure(state=state)

    def _sync_delete_btn(self, *_: object) -> None:
        """Mirror is_delete_btn_enabled_var onto the Supprimer button."""
        state = tk.NORMAL if self._vm.is_delete_btn_enabled_var.get() else tk.DISABLED
        self._btn_delete.configure(state=state)

    def _sync_save_btn(self, *_: object) -> None:
        """Mirror is_save_btn_enabled_var onto the Sauvegarder button."""
        state = tk.NORMAL if self._vm.is_save_btn_enabled_var.get() else tk.DISABLED
        self._btn_save.configure(state=state)

    def _sync_path_entry(self, *_: object) -> None:
        """Enable or disable the path entry and its browse button."""
        if not self._vm.is_profile_section_enabled_var.get():
            self._entry_source_path.configure(state=tk.DISABLED)
            self._btn_browse_source.configure(state=tk.DISABLED)
            return
        state = tk.NORMAL if self._vm.is_path_entry_enabled_var.get() else tk.DISABLED
        self._entry_source_path.configure(state=state)
        self._btn_browse_source.configure(state=state)

    def _sync_sort_order(self, *_: object) -> None:
        """Enable or disable the sort-order radio buttons."""
        if not self._vm.is_profile_section_enabled_var.get():
            self._rb_recent.state(["disabled"])
            self._rb_oldest.state(["disabled"])
            return
        rb_state = ["!disabled"] if self._vm.is_sort_order_enabled_var.get() else ["disabled"]
        self._rb_recent.state(rb_state)
        self._rb_oldest.state(rb_state)

    def _sync_preview_editable(self, *_: object) -> None:
        """Switch the URL preview Text widget between editable and read-only."""
        if not self._vm.is_profile_section_enabled_var.get():
            self._txt_url_preview.configure(state=tk.DISABLED)
            return
        editable = self._vm.is_preview_editable_var.get()
        if editable:
            self._txt_url_preview.configure(state=tk.NORMAL)
        else:
            self._txt_url_preview.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Dialog helpers — owned by View (require parent=self)
    # ------------------------------------------------------------------

    def show_error(self, title: str, message: str) -> None:
        """Display a modal error dialog.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        messagebox.showerror(title, message, parent=self)

    # ------------------------------------------------------------------
    # Private event handlers — delegate to ViewModel action methods
    # ------------------------------------------------------------------

    def _on_combo_scenario_changed(self, _event: tk.Event) -> None:
        obj = self._combo_scenarios.get_selected_object()
        if obj and isinstance(obj, ScenarioItem):
            self._vm.scenario_changed(obj.id_file)

    def _on_refresh_clicked(self) -> None:
        if self._refresh_cooldown:
            return
        self._refresh_cooldown = True
        self.after(1000, self._reset_refresh_cooldown)
        self._vm.refresh_scenarios()

    def _reset_refresh_cooldown(self) -> None:
        self._refresh_cooldown = False

    def _on_edit_clicked(self) -> None:
        obj = self._combo_scenarios.get_selected_object()
        if obj and isinstance(obj, ScenarioItem):
            self._vm.edit_scenario(obj.id_file)

    def _on_listbox_profile_selected(self, _event: tk.Event) -> None:
        sel = self._listbox_profiles.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self._profile_items):
            self._vm.profile_selected(self._profile_items[idx].id_profile)

    def _on_new_clicked(self) -> None:
        name = simpledialog.askstring("Nouveau profil", "Nom du profil :", initialvalue="", parent=self)
        if name and name.strip():
            self._vm.new_profile(name.strip())

    def _on_rename_clicked(self) -> None:
        current = self._vm.current_profile_name_var.get()
        new_name = simpledialog.askstring("Renommer le profil", "Nouveau nom :", initialvalue=current, parent=self)
        if new_name and new_name.strip() != current:
            self._vm.rename_profile(new_name.strip())

    def _on_delete_clicked(self) -> None:
        name = self._vm.current_profile_name_var.get()
        confirmed = messagebox.askyesno(
            "Supprimer le profil", f"Supprimer le profil « {name} » ?\nCette action est irréversible.", parent=self
        )
        if confirmed:
            self._vm.delete_profile()

    def _on_step_selected(self, _event: tk.Event) -> None:
        idx = self._combo_steps.current()
        if 0 <= idx < len(self._step_items):
            # Silently update the ViewModel Var without re-triggering form_changed.
            self._vm.step_id_selected_var.set(self._step_items[idx].step_id)
        self._vm.form_changed()

    def _on_source_type_changed(self, _event: tk.Event) -> None:
        idx = self._combo_source.current()
        if 0 <= idx < len(self._source_choices):
            self._vm.url_source_type_var.set(self._source_choices[idx][1])
        self._vm.form_changed()

    def _on_url_text_modified(self, _event: tk.Event) -> None:
        if self._txt_url_preview.edit_modified():
            self._txt_url_preview.edit_modified(False)
            content = self._txt_url_preview.get("1.0", tk.END)
            self._vm.manual_urls_var.set(content)
            self._vm.form_changed()

    def _browse_export_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier d'export", parent=self)
        if folder:
            self._vm.export_folder_var.set(folder)

    def _browse_source_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier source d'URL", parent=self)
        if folder:
            self._vm.url_source_path_var.set(folder)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _set_url_preview_text(self, text: str, *, editable: bool) -> None:
        """Replace the content of the URL text widget.

        Args:
            text: The text to write into the widget.
            editable: When True the widget accepts typing; otherwise read-only.
        """
        self._txt_url_preview.configure(state=tk.NORMAL)
        self._txt_url_preview.delete("1.0", tk.END)
        self._txt_url_preview.insert("1.0", text)
        self._txt_url_preview.edit_modified(False)
        if not editable:
            self._txt_url_preview.configure(state=tk.DISABLED)


# EOF
