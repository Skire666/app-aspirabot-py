"""Tkinter view for the executor panel.

Passive widget tree bound to ``ExecutorViewModel``.  All widget state is
driven by ViewModel Vars; all user actions are forwarded to the ViewModel
action methods.  No business logic, no service calls.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, cast

from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem, StepItem
from views.components.column_combobox.column_combobox import ColumnCombobox
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame
from views.executor.url_config_view import UrlConfigView

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ExecutorView(ttk.Frame):
    """Panel that lets the user configure and launch a scraping session.

    Sections:
        1. Scenario selection (ColumnCombobox + Refresh + Edit buttons).
        2. Available profiles (Listbox + CRUD buttons + saved-date label).
        3a. Basic scenario settings (HorizontalLineFrame: dates, export folder, thresholds).
        3b. URL settings (HorizontalLineFrame containing UrlConfigView with a notebook).
        4. Launch trigger (verification label + launch button).

    The view is purely passive: every widget is bound to a ``ExecutorViewModel``
    Var or reacts to a version-trigger Var via ``trace_add``.
    """

    def __init__(self, parent: tk.Widget, vm: ExecutorViewModel) -> None:
        """Build widget structure and bind to the ViewModel.

        Args:
            parent: Parent Tkinter container.
            vm: The ViewModel that owns all UI state for this panel.
            discover_presenter: DiscoverPresenter for the URL-config tab-4 discover panel.
        """
        super().__init__(parent)
        self._vm = vm
        self._view_traces: list[tuple[tk.Variable, str]] = []

        # Local rendering caches — refreshed from VM list data on version changes.
        self._profile_items: list[ProfileItem] = []
        self._step_items: list[StepItem] = []

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
        """Build all sections in order."""
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True)
        self._create_launch_section(outer)  # footer
        self._create_scenario_section(outer)
        self._create_profiles_section(outer)
        self._create_basic_settings_section(outer)
        self._create_url_settings_section(outer)

    def _create_scenario_section(self, parent: tk.Widget) -> None:
        """Build the scenario selection section."""
        frame = HorizontalLineFrame(parent, text="Liste des scénarios")
        frame.pack(fill=tk.X)

        self._btn_edit = ttk.Button(frame, text="Modifier", command=self._on_edit_clicked)
        self._btn_edit.pack(side=tk.RIGHT, padx=(0, 5))

        self._btn_refresh = ttk.Button(frame, text="Rafraîchir", command=self._on_refresh_clicked)
        self._btn_refresh.pack(side=tk.RIGHT, padx=(0, 5))

        self._combo_scenarios = ColumnCombobox(frame)
        self._combo_scenarios.add_column("scenario_name", lambda m: m.scenario_name, width=140)
        self._combo_scenarios.add_column("scenario_desc", lambda m: m.scenario_desc, width=240)
        self._combo_scenarios.add_column("id_file", lambda m: m.id_file, width=25)
        self._combo_scenarios.set_display_column("scenario_name")
        self._combo_scenarios.bind("<<ComboboxSelected>>", self._on_combo_scenario_changed)
        self._combo_scenarios.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6))

    def _create_profiles_section(self, parent: tk.Widget) -> None:
        """Build the available-profiles section."""
        frame = HorizontalLineFrame(parent, text="Profils disponibles")
        frame.pack(fill=tk.X)

        self._listbox_profiles = tk.Listbox(
            frame, height=5, selectmode=tk.SINGLE, exportselection=False, activestyle="none"
        )
        self._listbox_profiles.pack(fill=tk.X, padx=5, pady=(0, 5))
        self._listbox_profiles.bind("<<ListboxSelect>>", self._on_listbox_profile_selected)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=(0, 5))

        self._btn_new = ttk.Button(btn_row, text="Nouveau", command=self._on_new_clicked)
        self._btn_new.pack(side=tk.LEFT, padx=5)

        self._btn_rename = ttk.Button(btn_row, text="Renommer", command=self._on_rename_clicked)
        self._btn_rename.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_delete = ttk.Button(btn_row, text="Supprimer", command=self._on_delete_clicked)
        self._btn_delete.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_save = ttk.Button(btn_row, text="Sauvegarder", command=lambda: self._vm.save_profile())
        self._btn_save.pack(side=tk.LEFT, padx=(0, 5))

        self._lbl_saved = ttk.Label(btn_row, textvariable=self._vm.saved_date_var)
        self._lbl_saved.pack(side=tk.RIGHT, padx=5)

    def _create_basic_settings_section(self, parent: tk.Widget) -> None:
        """Build the basic scenario settings section (dates, export folder, thresholds)."""
        frame = HorizontalLineFrame(parent, text="Réglage du scénario")
        frame.pack(fill=tk.X)
        container = ttk.Frame(frame)
        container.pack(fill=tk.X)
        self._basic_settings_grid = container
        self._create_cfg_row0(container)
        self._create_cfg_row1(container)
        self._create_cfg_row5(container)
        self._create_cfg_row6(container)
        self._create_cfg_row_warmup(container)

    def _create_url_settings_section(self, parent: tk.Widget) -> None:
        """Build the URL settings section containing the UrlConfigView notebook."""
        frame = HorizontalLineFrame(parent, text="Réglage des URLs")
        frame.pack(fill=tk.X)
        self._url_config_view = UrlConfigView(frame, vm=self._vm)
        self._url_config_view.pack(fill=tk.BOTH, expand=True)

    def _create_cfg_row0(self, parent: tk.Widget) -> None:
        """Row 0 — usage statistics (last used date, launch count)."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Dernier usage :").pack(side=tk.LEFT, padx=(5, 16), pady=(0, 5))
        ttk.Label(row, textvariable=self._vm.used_date_var).pack(side=tk.LEFT, padx=(0, 30), pady=(0, 5))
        ttk.Label(row, text="Lancements :").pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
        ttk.Label(row, textvariable=self._vm.launch_count_var).pack(side=tk.LEFT, pady=(0, 5))

    def _create_cfg_row1(self, parent: tk.Widget) -> None:
        """Row 1 — export folder path, browse button, open-folder button."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Dossier d'export :").pack(side=tk.LEFT, padx=5, pady=(0, 5))

        FolderLinkWidget(row, title="", path="Ouvrir le dossier", callback=lambda: self._vm.open_export_folder()).pack(
            side=tk.RIGHT, padx=(0, 10), pady=(0, 5)
        )
        ttk.Button(row, text="Parcourir", command=self._browse_export_folder).pack(
            side=tk.RIGHT, padx=(0, 5), pady=(0, 5)
        )
        self._view_traces.append(
            (
                self._vm.export_folder_var,
                self._vm.export_folder_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.export_folder_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(0, 5)
        )

    def _create_cfg_row5(self, parent: tk.Widget) -> None:
        """Row 5 — global error threshold."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Erreurs globales max. avant mise en pause d'urgence :").pack(
            side=tk.LEFT, padx=5, pady=(0, 6)
        )
        self._view_traces.append(
            (
                self._vm.global_threshold_var,
                self._vm.global_threshold_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.global_threshold_var, width=12).pack(side=tk.LEFT, pady=(0, 6))

    def _create_cfg_row6(self, parent: tk.Widget) -> None:
        """Row 6 — per-step error threshold with step selector."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Mettre en pause l'étape :").pack(side=tk.LEFT, padx=5, pady=6)
        self._combo_steps = ttk.Combobox(row, state="readonly", width=35)
        self._combo_steps.pack(side=tk.LEFT, padx=(0, 5), pady=6)
        self._combo_steps.bind("<<ComboboxSelected>>", self._on_step_selected)
        self._view_traces.append(
            (
                self._vm.step_threshold_var,
                self._vm.step_threshold_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Label(row, text=" après  ").pack(side=tk.LEFT, padx=(0, 5), pady=6)
        ttk.Entry(row, textvariable=self._vm.step_threshold_var, width=10).pack(side=tk.LEFT, padx=(0, 5), pady=6)
        ttk.Label(row, text="erreurs").pack(side=tk.LEFT, padx=(0, 5), pady=6)

    def _create_cfg_row_warmup(self, parent: tk.Widget) -> None:
        """Warmup URL row — optional URL loaded before the scraping run starts."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Préchauffe URL : ").pack(side=tk.LEFT, padx=5, pady=(6, 0))
        self._view_traces.append(
            (self._vm.warmup_url_var, self._vm.warmup_url_var.trace_add("write", lambda *_: self._vm.form_changed()))
        )
        ttk.Entry(row, textvariable=self._vm.warmup_url_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(6, 0)
        )

    def _create_launch_section(self, parent: tk.Widget) -> None:
        """Build the launch-trigger section."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, side=tk.BOTTOM, padx=5)

        ttk.Label(row, text="Vérification :").pack(side=tk.LEFT, padx=0, pady=6)
        ttk.Label(row, textvariable=self._vm.verification_message_var, foreground="red").pack(
            side=tk.LEFT, fill=tk.X, expand=True, pady=6
        )

        self._btn_launch = ttk.Button(row, text="Lancer le scraping", width=25, command=lambda: self._vm.launch())
        self._btn_launch.pack(side=tk.RIGHT, padx=(10, 0), pady=6)

    # ------------------------------------------------------------------
    # ViewModel bindings (trace_add for non-Var widgets)
    # ------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace listeners for all non-Var widget bindings; ids stored for teardown."""
        bindings: list[tuple[tk.Variable, Callable[..., object]]] = [
            (self._vm.scenarios_version_var, self._sync_scenarios),
            (self._vm.selected_scenario_id_var, self._sync_scenario_selection),
            (self._vm.profiles_version_var, self._sync_profiles),
            (self._vm.selected_profile_id_var, self._sync_profile_selection),
            (self._vm.steps_version_var, self._sync_steps),
            (self._vm.step_id_selected_var, self._sync_step_selection),
            (self._vm.is_profiles_list_enabled_var, self._sync_profiles_list_enabled),
            (self._vm.is_profile_section_active_var, self._sync_profile_section_enabled),
            (self._vm.is_edit_btn_enabled_var, self._sync_edit_btn),
            (self._vm.is_rename_btn_enabled_var, self._sync_rename_btn),
            (self._vm.is_delete_btn_enabled_var, self._sync_delete_btn),
            (self._vm.is_save_btn_enabled_var, self._sync_save_btn),
        ]
        for var, cb in bindings:
            self._view_traces.append((var, var.trace_add("write", cb)))
        self._apply_initial_state()

    def teardown(self) -> None:
        """Detach all view-owned VM traces, teardown child views, and dispose the ViewModel."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()
        self._url_config_view.teardown()
        self._vm.dispose()

    def _apply_initial_state(self) -> None:
        self._sync_profiles_list_enabled()
        self._sync_profile_section_enabled()
        self._sync_edit_btn()
        self._sync_rename_btn()
        self._sync_delete_btn()
        self._sync_save_btn()

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

    def _sync_profiles_list_enabled(self, *_: object) -> None:
        """Enable or disable the profile listbox and Nouveau button."""
        state = tk.NORMAL if self._vm.is_profiles_list_enabled_var.get() else tk.DISABLED
        self._listbox_profiles.configure(state=state)
        self._btn_new.configure(state=state)

    def _sync_profile_section_enabled(self, *_: object) -> None:
        """Enable or disable the basic-settings section widgets."""
        enabled = self._vm.is_profile_section_active_var.get()

        def _apply(widget: tk.Widget) -> None:
            for child in widget.winfo_children():
                with contextlib.suppress(tk.TclError):
                    w: Any = child
                    if not enabled:
                        w.configure(state=tk.DISABLED)
                    elif isinstance(child, ttk.Combobox):
                        w.configure(state="readonly")
                    else:
                        w.configure(state=tk.NORMAL)
                _apply(child)  # type: ignore[arg-type]

        _apply(self._basic_settings_grid)

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
        self.after(500, self._reset_refresh_cooldown)
        self._vm.refresh_scenarios()

    def _reset_refresh_cooldown(self) -> None:
        self._refresh_cooldown = False

    def _on_edit_clicked(self) -> None:
        obj = self._combo_scenarios.get_selected_object()
        if obj and isinstance(obj, ScenarioItem):
            self._vm.edit_scenario(obj.id_file)

    def _on_listbox_profile_selected(self, _event: tk.Event) -> None:
        sel: tuple[int, ...] = self._listbox_profiles.curselection()  # type: ignore[reportUnknownMemberType]
        if not sel:
            return
        idx: int = cast(int, sel[0])
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

    def _browse_export_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier d'export", parent=self)
        if folder:
            self._vm.export_folder_var.set(folder)


# EOF
