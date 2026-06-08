"""Passive Tkinter view for the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from presenters.discover_presenter import DiscoverPresenter
from view_models.discover_view_model import DiscoverViewModel
from views.components.column_combobox.column_combobox import ColumnCombobox
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DiscoverView(ttk.Frame):
    """Panel for the Discover module: project management, input/output config, profile update.

    Sections:
        0. Project management (Cadre 0).
        1. Input — discover links (Cadre 1).
        2. Output — single sheet (Cadre 2).
        3. Profile update (Cadre 3).

    Purely passive: all state comes from DiscoverViewModel Vars;
    all user actions are forwarded to the VM action methods.
    """

    def __init__(self, parent: tk.Widget, vm: DiscoverViewModel, presenter: DiscoverPresenter) -> None:
        """Build all sections and register VM bindings.

        Args:
            parent: Parent Tkinter container.
            vm: ViewModel owning all UI state.
            presenter: Presenter providing project/profile selection callbacks.
        """
        super().__init__(parent)
        self._vm = vm
        self._presenter = presenter
        self._view_traces: list[tuple[tk.Variable, str]] = []

        self._create_widgets()
        self._bind_vm_collections()

    # -------------------------------------------------------------------------
    # Widget construction
    # -------------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build a scrollable container hosting the four sections."""
        # Outer scrollable canvas
        self._inner = tk.Frame(self, borderwidth=0)
        self._inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._create_section_project(self._inner)
        self._create_section_input(self._inner)
        self._create_section_output(self._inner)
        self._create_section_profile(self._inner)

    # ─── Cadre 0 : project management ─────────────────────────────────────────

    def _create_section_project(self, parent: tk.Frame) -> None:
        """Build the project creation and management section."""
        frame = HorizontalLineFrame(parent, text="Créer un projet")
        frame.pack(fill=tk.X)

        # Ligne 0 : name + create
        row0 = ttk.Frame(frame)
        row0.pack(fill=tk.X, padx=4)
        self._btn_create = ttk.Button(row0, text="Créer", command=self._vm.create_project)
        self._btn_create.pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Label(row0, text="Nom du projet :").pack(side=tk.LEFT, pady=(2, 6))
        ttk.Entry(row0, textvariable=self._vm.new_project_name_var, width=30).pack(fill=tk.X, padx=(6, 0), pady=(6, 0))

        # Ligne 1 : listbox
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, padx=4, pady=(4, 0))
        self._listbox_projects = tk.Listbox(row1, height=5, selectmode=tk.SINGLE, exportselection=False)
        self._listbox_projects.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._listbox_projects.bind("<<ListboxSelect>>", self._on_listbox_project_select)

        # Ligne 2 : rename / delete / save / date
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, padx=4, pady=(6, 4))
        self._btn_rename = ttk.Button(row2, text="Renommer la sélection", command=self._on_rename_clicked)
        self._btn_rename.pack(side=tk.LEFT, padx=(0, 4))
        self._btn_delete = ttk.Button(row2, text="Supprimer la sélection", command=self._on_delete_clicked)
        self._btn_delete.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row2, textvariable=self._vm.saved_date_var).pack(side=tk.RIGHT, padx=(4, 0))
        self._btn_save_project = ttk.Button(row2, text="Sauvegarder le projet", command=self._vm.save_project)
        self._btn_save_project.pack(side=tk.RIGHT, padx=6)

        # Traces: sync button states from derived vars
        self._add_trace(self._vm.can_create_project_var, lambda *_: self._sync_create_btn())
        self._add_trace(self._vm.can_action_project_var, lambda *_: self._sync_action_btns())
        self._add_trace(self._vm.can_save_project_var, lambda *_: self._sync_save_btn())
        self._sync_create_btn()
        self._sync_action_btns()
        self._sync_save_btn()

    # ─── Cadre 1 : input section ───────────────────────────────────────────────

    def _create_section_input(self, parent: tk.Frame) -> None:
        """Build the input JSON discovery section."""
        frame = HorizontalLineFrame(parent, text="Entrée - Découverte les liens")
        frame.pack(fill=tk.X)

        # Ligne 0 : folder path
        row0 = ttk.Frame(frame)
        row0.pack(fill=tk.X, padx=4)
        # Pack RIGHT widgets first so Entry can fill the remaining middle space.
        self._input_folder_link = FolderLinkWidget(
            row0, title="", path="Ouvrir dossier", callback=self._vm.open_input_folder
        )
        self._input_folder_link.pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(row0, text="Parcourir", command=self._on_browse_input_clicked).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Label(row0, text="Dossier JSON :", width=14).pack(side=tk.LEFT)
        ttk.Entry(row0, textvariable=self._vm.input_folder_json_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0)
        )

        # Ligne 1 : JSON pattern + file count verification
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, padx=4)
        ttk.Label(row1, textvariable=self._vm.input_files_check_var, width=15).pack(side=tk.RIGHT, padx=(4, 0), pady=6)
        ttk.Label(row1, text="Vérification :").pack(side=tk.RIGHT, padx=(50, 0), pady=6)
        ttk.Label(row1, text="Regexp fichiers :").pack(side=tk.LEFT, padx=(0, 0), pady=6)
        ttk.Entry(row1, textvariable=self._vm.input_pattern_json_var).pack(fill=tk.X, padx=(6, 0), pady=6)

        # Ligne 2 : key + URL pattern + URL count verification
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, padx=4)
        ttk.Label(row2, textvariable=self._vm.input_urls_check_var, width=15).pack(side=tk.RIGHT, padx=(4, 0), pady=6)
        ttk.Label(row2, text="Vérification :").pack(side=tk.RIGHT, padx=(50, 0), pady=6)
        ttk.Label(row2, text="Clé/mapping :", width=14).pack(side=tk.LEFT, pady=6)
        ttk.Entry(row2, textvariable=self._vm.input_key_mapping_var, width=15).pack(side=tk.LEFT, padx=(6, 0), pady=6)
        ttk.Label(row2, text="Regexp URLs :").pack(side=tk.LEFT, padx=(30, 0), pady=6)
        ttk.Entry(row2, textvariable=self._vm.input_pattern_urls_var, width=24).pack(side=tk.LEFT, padx=(6, 0), pady=6)

    # ─── Cadre 2 : output section ──────────────────────────────────────────────

    def _create_section_output(self, parent: tk.Frame) -> None:
        """Build the output JSON discovery section."""
        frame = HorizontalLineFrame(parent, text="Sortie - Fiche unique")
        frame.pack(fill=tk.X)

        # Ligne 0 : folder path
        row0 = ttk.Frame(frame)
        row0.pack(fill=tk.X, padx=4)
        # Pack RIGHT widgets first so Entry can fill the remaining middle space.
        self._output_folder_link = FolderLinkWidget(
            row0, title="", path="Ouvrir dossier", callback=self._vm.open_output_folder
        )
        self._output_folder_link.pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(row0, text="Parcourir", command=self._on_browse_output_clicked).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Label(row0, text="Dossier JSON :", width=14).pack(side=tk.LEFT)
        ttk.Entry(row0, textvariable=self._vm.output_folder_json_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0)
        )

        # Ligne 1 : JSON pattern + file count verification
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, padx=4)
        ttk.Label(row1, textvariable=self._vm.output_files_check_var, width=15).pack(side=tk.RIGHT, padx=(4, 0), pady=6)
        ttk.Label(row1, text="Vérification :").pack(side=tk.RIGHT, padx=(50, 0), pady=6)
        ttk.Label(row1, text="Regexp fichiers :").pack(side=tk.LEFT, padx=(0, 0), pady=6)
        ttk.Entry(row1, textvariable=self._vm.output_pattern_json_var).pack(fill=tk.X, padx=(6, 0), pady=6)

        # Ligne 2 : key + URL pattern + URL count verification
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, padx=4)
        ttk.Label(row2, textvariable=self._vm.output_urls_check_var, width=15).pack(side=tk.RIGHT, padx=(4, 0), pady=6)
        ttk.Label(row2, text="Vérification :").pack(side=tk.RIGHT, padx=(50, 0), pady=6)
        ttk.Label(row2, text="Clé/mapping :", width=14).pack(side=tk.LEFT, pady=6)
        ttk.Entry(row2, textvariable=self._vm.output_key_mapping_var, width=15).pack(side=tk.LEFT, padx=(6, 0), pady=6)
        ttk.Label(row2, text="Regexp URLs :").pack(side=tk.LEFT, padx=(30, 0), pady=6)
        ttk.Entry(row2, textvariable=self._vm.output_pattern_urls_var, width=24).pack(side=tk.LEFT, padx=(6, 0), pady=6)

    # ─── Cadre 3 : profile update ──────────────────────────────────────────────

    def _create_section_profile(self, parent: tk.Frame) -> None:
        """Build the profile update section."""
        self._frame_profile = HorizontalLineFrame(parent, text="Mise à jour du profil")
        self._frame_profile.pack(fill=tk.X)

        # Ligne 0 : profile combobox
        row0 = ttk.Frame(self._frame_profile)
        row0.pack(fill=tk.X, padx=4)
        ttk.Label(row0, text="Choisir le profil :", width=15).pack(side=tk.LEFT, padx=(0, 0))
        self._combo_profiles = ColumnCombobox(row0, width=28)
        self._combo_profiles.add_column("profile_name", lambda r: r.profile_name, width=160)
        self._combo_profiles.add_column("scenario_name", lambda r: r.scenario_name, width=140)
        self._combo_profiles.add_column("id_profile", lambda r: r.id_profile, width=80)
        self._combo_profiles.set_display_column("profile_name")
        self._combo_profiles.bind("<<ComboboxSelected>>", self._on_profile_selected)
        self._combo_profiles.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # Ligne 1 : profile name + save list button
        row1 = ttk.Frame(self._frame_profile)
        row1.pack(fill=tk.X, padx=4, pady=(6, 0))
        ttk.Label(row1, text="Nom du profil :", width=15).pack(side=tk.LEFT, padx=(0, 0))
        ttk.Entry(row1, textvariable=self._vm.profile_name_template_var, width=30).pack(side=tk.LEFT, padx=(6, 0))
        self._btn_save_list = ttk.Button(row1, text="Sauvegarder la liste", command=self._vm.save_profile_list)
        self._btn_save_list.pack(side=tk.LEFT, padx=(12, 0))
        ttk.Label(row1, textvariable=self._vm.save_profile_hint_var).pack(side=tk.LEFT, padx=(8, 0))

        # Ligne 2 : save result label
        row2 = ttk.Frame(self._frame_profile)
        row2.pack(fill=tk.X, padx=4)
        ttk.Label(row2, text="Résultat sauvegarde").pack(side=tk.LEFT, padx=(0, 6), pady=6)
        ttk.Label(row2, textvariable=self._vm.profile_save_result_var).pack(side=tk.LEFT, padx=(6, 0), pady=6)

        self._add_trace(self._vm.can_update_profile_var, lambda *_: self._sync_save_list_btn())
        self._sync_save_list_btn()

    # -------------------------------------------------------------------------
    # VM collection bindings
    # -------------------------------------------------------------------------

    def _bind_vm_collections(self) -> None:
        """Register callbacks so the View re-renders collections on change."""
        self._vm.bind_projects_changed(self._on_projects_changed)
        self._vm.bind_profiles_changed(self._on_profiles_changed)

    def _on_projects_changed(self) -> None:
        """Re-render the projects listbox from vm.projects."""
        self._listbox_projects.delete(0, tk.END)
        selected_id = self._vm.selected_project_id_var.get()
        selected_idx: int | None = None
        for i, row in enumerate(self._vm.projects):
            self._listbox_projects.insert(tk.END, row.project_name)
            if row.id_discover == selected_id:
                selected_idx = i
        if selected_idx is None and self._vm.projects:
            selected_idx = 0
        if selected_idx is not None:
            self._listbox_projects.selection_set(selected_idx)
            self._listbox_projects.see(selected_idx)

    def _on_profiles_changed(self) -> None:
        """Re-render the profiles ColumnCombobox from vm.profiles."""
        self._combo_profiles.clear()
        selected_id = self._vm.profile_id_scenario_var.get()
        selected_idx: int | None = None
        for i, row in enumerate(self._vm.profiles):
            self._combo_profiles.add_item(row)
            if row.id_scenario == selected_id:
                selected_idx = i
        if selected_idx is not None:
            self._combo_profiles.current(selected_idx)

    # -------------------------------------------------------------------------
    # Event handlers (UI logic only — no business decisions)
    # -------------------------------------------------------------------------

    def _on_listbox_project_select(self, event: Any) -> None:  # noqa: ANN401
        """Handle listbox selection change; restore highlight if Tkinter cleared it."""
        selection = self._listbox_projects.curselection()
        if not selection:
            projects = self._vm.projects
            if not projects:
                return
            selected_id = self._vm.selected_project_id_var.get()
            restore_idx = next((i for i, r in enumerate(projects) if r.id_discover == selected_id), 0)
            self._listbox_projects.selection_set(restore_idx)
            return
        idx = selection[0]
        projects = self._vm.projects
        if 0 <= idx < len(projects):
            self._presenter.on_project_selected(projects[idx].id_discover)

    def _on_rename_clicked(self) -> None:
        """Ask for a new name and dispatch rename_project via the VM."""
        new_name = simpledialog.askstring("Renommer le projet", "Nouveau nom du projet :", parent=self)
        if new_name and new_name.strip():
            self._vm.new_project_name_var.set(new_name.strip())
            self._vm.rename_project()

    def _on_delete_clicked(self) -> None:
        """Ask for confirmation then dispatch delete_project via the VM."""
        projects = self._vm.projects
        selected_id = self._vm.selected_project_id_var.get()
        name = next((r.project_name for r in projects if r.id_discover == selected_id), selected_id)
        confirmed = messagebox.askyesno(
            "Supprimer le projet", f"Êtes-vous sûr de vouloir supprimer le projet '{name}' ?", parent=self
        )
        if confirmed:
            self._vm.delete_project()

    def _on_browse_input_clicked(self) -> None:
        """Open a folder dialog and write the result to input_folder_json_var."""
        folder = filedialog.askdirectory(parent=self, title="Sélectionner le dossier JSON d'entrée")
        if folder:
            self._vm.input_folder_json_var.set(folder)

    def _on_browse_output_clicked(self) -> None:
        """Open a folder dialog and write the result to output_folder_json_var."""
        folder = filedialog.askdirectory(parent=self, title="Sélectionner le dossier JSON de sortie")
        if folder:
            self._vm.output_folder_json_var.set(folder)

    def _on_profile_selected(self, event: Any) -> None:  # noqa: ANN401
        """Handle combobox selection and notify the presenter."""
        row = self._combo_profiles.get_selected_object()
        self._presenter.on_profile_selected(row)

    # -------------------------------------------------------------------------
    # Button state sync (mirrors derived Vars)
    # -------------------------------------------------------------------------

    def _sync_create_btn(self) -> None:
        """Enable/disable the Create button based on can_create_project_var."""
        state = tk.NORMAL if self._vm.can_create_project_var.get() else tk.DISABLED
        self._btn_create.configure(state=state)

    def _sync_action_btns(self) -> None:
        """Enable/disable Rename and Delete buttons based on can_action_project_var."""
        state = tk.NORMAL if self._vm.can_action_project_var.get() else tk.DISABLED
        self._btn_rename.configure(state=state)
        self._btn_delete.configure(state=state)

    def _sync_save_btn(self) -> None:
        """Enable/disable the Save project button based on can_save_project_var."""
        state = tk.NORMAL if self._vm.can_save_project_var.get() else tk.DISABLED
        self._btn_save_project.configure(state=state)

    def _sync_save_list_btn(self) -> None:
        """Enable/disable the Save-list button based on can_update_profile_var."""
        state = tk.NORMAL if self._vm.can_update_profile_var.get() else tk.DISABLED
        self._btn_save_list.configure(state=state)

    # -------------------------------------------------------------------------
    # Trace helpers (View-owned, detached on teardown)
    # -------------------------------------------------------------------------

    def _add_trace(self, var: tk.Variable, callback: Any) -> None:  # noqa: ANN401
        """Register a write-trace and remember it for teardown.

        Args:
            var: The Tkinter variable to watch.
            callback: The callback to invoke on write.
        """
        trace_id = var.trace_add("write", callback)
        self._view_traces.append((var, trace_id))

    # -------------------------------------------------------------------------
    # Teardown
    # -------------------------------------------------------------------------

    def teardown(self) -> None:
        """Detach all View-owned traces before the VM is disposed."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()


# EOF
