"""Passive widget tree for the Découvrir module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from view_models.discover_view_model import DiscoverViewModel, ProfileRowState
from views.components.column_combobox.column_combobox import ColumnCombobox
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DiscoverView(ttk.Frame):
    """Passive widget tree bound to DiscoverViewModel.

    Layout: four HorizontalLineFrame sections stacked vertically in a scrolled
    canvas. Each section contains a ttk.Frame container for grid layout.

    Section 0 — Project management (create, select from list, rename/delete/save).
    Section 1 — Input folder/pattern/regexp + compute-inputs + preview.
    Section 2 — Output folder/pattern/regexp + compute-outputs + preview.
    Section 3 — Profile selection, name, save (disabled until both compute succeed).
    """

    def __init__(self, master: tk.Misc, vm: DiscoverViewModel) -> None:
        """Build the full widget tree and wire all VM bindings.

        Args:
            master: Parent Tkinter widget.
            vm: DiscoverViewModel instance to bind against.
        """
        super().__init__(master)
        self._vm = vm

        # Outer scrollable area
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Build all sections
        self._build_frame0()
        self._build_frame1()
        self._build_frame2()
        self._build_frame3()

        # Register collection observers (View side)
        vm.bind_projects_changed(self._on_projects_changed)
        vm.bind_profiles_changed(self._on_profiles_changed)

        # Track view-owned traces for teardown
        self._frame3_widgets: list[tk.Widget] = []
        self._frame3_trace_id = vm.is_frame3_enabled_var.trace_add("write", self._sync_frame3_state)
        self._can_create_trace_id = vm.can_create_project_var.trace_add("write", self._sync_create_btn)
        self._can_save_project_trace_id = vm.can_save_project_var.trace_add("write", self._sync_save_project_btn)
        self._can_save_profile_trace_id = vm.can_save_profile_var.trace_add("write", self._sync_save_profile_btn)
        self._can_manage_trace_id = vm.can_manage_project_var.trace_add("write", self._sync_manage_btns)

        # Initial sync
        self._sync_frame3_state()
        self._sync_create_btn()
        self._sync_save_project_btn()
        self._sync_save_profile_btn()
        self._sync_manage_btns()

    # =========================================================================
    # Section 0 — Project management
    # =========================================================================

    def _build_frame0(self) -> None:
        """Build the 'Créer un projet' section."""
        section = HorizontalLineFrame(self._inner, text="Créer un projet")
        section.pack(fill="x")

        frame = ttk.Frame(section, padding=(8, 0, 8, 0))
        frame.pack(fill="x")
        frame.columnconfigure(1, weight=1)

        # Row 0 — name entry + create button
        ttk.Label(frame, text="Nom du projet :").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(frame, textvariable=self._vm.project_name_input_var).grid(row=0, column=1, sticky="ew")
        self._create_btn = ttk.Button(frame, text="Créer", command=self._vm.create_project)
        self._create_btn.grid(row=0, column=2, padx=(6, 0))

        # Row 1 — project listbox (scrolled)
        listbox_frame = ttk.Frame(frame)
        listbox_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        listbox_frame.columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical")
        self._project_listbox = tk.Listbox(
            listbox_frame, yscrollcommand=scrollbar.set, selectmode="single", height=5, exportselection=False
        )
        scrollbar.configure(command=self._project_listbox.yview)
        self._project_listbox.grid(row=0, column=0, sticky="ew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._project_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Row 2 — action bar: [Renommer] [Supprimer] ... [Sauvegardé le : --] [Sauvegarder]
        action_row = ttk.Frame(frame)
        action_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        self._rename_btn = ttk.Button(action_row, text="Renommer la sélection", command=self._vm.rename_project)
        self._rename_btn.pack(side="left")
        self._delete_btn = ttk.Button(action_row, text="Supprimer la sélection", command=self._vm.delete_project)
        self._delete_btn.pack(side="left", padx=(6, 0))

        self._save_project_btn = ttk.Button(action_row, text="Sauvegarder le projet", command=self._vm.save_project)
        self._save_project_btn.pack(side="right")
        ttk.Label(action_row, textvariable=self._vm.last_save_date_var).pack(side="right", padx=(0, 10))

    # =========================================================================
    # Section 1 — Input discovery
    # =========================================================================

    def _build_frame1(self) -> None:
        """Build the 'Entrée - Découvrir les liens' section."""
        section = HorizontalLineFrame(self._inner, text="Entrée - Découvrir les liens")
        section.pack(fill="x")

        frame = ttk.Frame(section, padding=(8, 0, 8, 0))
        frame.pack(fill="x")
        frame.columnconfigure(1, weight=1)

        # Row 0 — input folder
        ttk.Label(frame, text="Dossier d'entrée des JSON :").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(frame, textvariable=self._vm.input_folder_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(frame, text="Parcourir", command=self._vm.browse_input_folder).grid(row=0, column=2, padx=(6, 0))

        # Row 1 — file pattern
        ttk.Label(frame, text="Pattern des fichiers :").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self._vm.input_pattern_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        # Row 2 — regexp URL entrée
        ttk.Label(frame, text="Regexp URL entrée :").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self._vm.regexp_url_input_var).grid(row=2, column=1, sticky="ew", pady=(6, 0))

        # Row 3 — compute button + counters
        compute_row = ttk.Frame(frame)
        compute_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(compute_row, text="Calculer les entrées", command=self._vm.compute_inputs).pack(side="left")
        ttk.Label(compute_row, textvariable=self._vm.input_node_count_var).pack(side="left", padx=(12, 0))
        ttk.Label(compute_row, textvariable=self._vm.input_value_count_var).pack(side="left", padx=(12, 0))

        # Row 4 — verification
        verif_row = ttk.Frame(frame)
        verif_row.grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(verif_row, textvariable=self._vm.input_verification_var, foreground="red").pack(side="left")

        # Row 5 — preview entrée
        preview_row = ttk.Frame(frame)
        preview_row.grid(row=5, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(preview_row, text="Preview entrée :").pack(side="left")
        ttk.Label(preview_row, textvariable=self._vm.preview_input_var, foreground="blue").pack(
            side="left", padx=(6, 0)
        )

    # =========================================================================
    # Section 2 — Output discovery
    # =========================================================================

    def _build_frame2(self) -> None:
        """Build the 'Sortie - Fiche par lien' section."""
        section = HorizontalLineFrame(self._inner, text="Sortie - Fiche par lien")
        section.pack(fill="x")

        frame = ttk.Frame(section, padding=(8, 0, 8, 0))
        frame.pack(fill="x")
        frame.columnconfigure(1, weight=1)

        # Row 0 — output folder
        ttk.Label(frame, text="Dossier de sortie des JSON :").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(frame, textvariable=self._vm.output_folder_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(frame, text="Parcourir", command=self._vm.browse_output_folder).grid(row=0, column=2, padx=(6, 0))

        # Row 1 — file pattern
        ttk.Label(frame, text="Pattern des fichiers :").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self._vm.output_pattern_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        # Row 2 — regexp URL sortie
        ttk.Label(frame, text="Regexp URL sortie :").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self._vm.regexp_url_output_var).grid(row=2, column=1, sticky="ew", pady=(6, 0))

        # Row 3 — compute button + counters
        compute_row = ttk.Frame(frame)
        compute_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(compute_row, text="Calculer les sorties", command=self._vm.compute_outputs).pack(side="left")
        ttk.Label(compute_row, textvariable=self._vm.output_node_count_var).pack(side="left", padx=(12, 0))
        ttk.Label(compute_row, textvariable=self._vm.output_value_count_var).pack(side="left", padx=(12, 0))

        # Row 4 — verification
        verif_row = ttk.Frame(frame)
        verif_row.grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(verif_row, textvariable=self._vm.output_verification_var, foreground="red").pack(side="left")

        # Row 5 — preview sortie
        preview_row = ttk.Frame(frame)
        preview_row.grid(row=5, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(preview_row, text="Preview sortie :").pack(side="left")
        ttk.Label(preview_row, textvariable=self._vm.preview_output_var, foreground="blue").pack(
            side="left", padx=(6, 0)
        )

    # =========================================================================
    # Section 3 — Profile update
    # =========================================================================

    def _build_frame3(self) -> None:
        """Build the 'Mise à jour du profil' section."""
        self._section3 = HorizontalLineFrame(self._inner, text="Mise à jour du profil")
        self._section3.pack(fill="x")

        self._frame3 = ttk.Frame(self._section3, padding=(8, 0, 8, 0))
        self._frame3.pack(fill="x")
        self._frame3.columnconfigure(1, weight=1)

        # Row 0 — profile ColumnCombobox (4 columns)
        ttk.Label(self._frame3, text="Choisir le profil :").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._profile_combo = ColumnCombobox(self._frame3)
        self._profile_combo.add_column("profile_name", lambda r: r.display_name, width=160)
        self._profile_combo.add_column("scenario", lambda r: r.scenario_name, width=130)
        self._profile_combo.add_column("id_scenario", lambda r: r.id_scenario, width=80)
        self._profile_combo.add_column("id_profile", lambda r: r.id_profile, width=80)
        self._profile_combo.set_display_column("profile_name")
        self._profile_combo.bind("<<ComboboxSelected>>", self._on_profile_combo_selected)
        self._profile_combo.grid(row=0, column=1, columnspan=2, sticky="ew")

        # Row 1 — profile name + save button
        ttk.Label(self._frame3, text="Nom du profil :").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(self._frame3, textvariable=self._vm.profile_name_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        self._save_profile_btn = ttk.Button(
            self._frame3, text="Sauvegarder la liste", command=self._vm.save_profile_list
        )
        self._save_profile_btn.grid(row=1, column=2, padx=(6, 0), pady=(6, 0))

        # Row 2 — save-profile status
        ttk.Label(self._frame3, textvariable=self._vm.save_profile_status_var, foreground="green").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )

        # Collect all frame3 children for enable/disable toggling
        # (ColumnCombobox is handled separately via set_enabled)
        self._collect_frame3_widgets()

    def _collect_frame3_widgets(self) -> None:
        """Collect interactive widgets inside frame3 for batch state toggling.

        ColumnCombobox is excluded here; it is toggled via set_enabled() in
        _sync_frame3_state to properly respect its internal disabled flag.
        """
        self._frame3_widgets = [
            w for w in self._frame3.winfo_children() if isinstance(w, (ttk.Entry, ttk.Button, ttk.Combobox, tk.Entry))
        ]
        for child in self._frame3.winfo_children():
            if isinstance(child, ttk.Frame):
                self._frame3_widgets.extend(
                    w for w in child.winfo_children() if isinstance(w, (ttk.Entry, ttk.Button, ttk.Combobox, tk.Entry))
                )

    # =========================================================================
    # Collection callbacks (View-side)
    # =========================================================================

    def _on_projects_changed(self) -> None:
        """Rebuild the project listbox from the current VM projects tuple."""
        selected_id = self._vm.selected_project_id_var.get()
        self._project_listbox.delete(0, "end")
        select_idx: int | None = None
        for idx, row in enumerate(self._vm.projects):
            self._project_listbox.insert("end", row.project_name)
            if row.id_project == selected_id:
                select_idx = idx
        if select_idx is not None:
            self._project_listbox.selection_set(select_idx)
            self._project_listbox.see(select_idx)

    def _on_profiles_changed(self) -> None:
        """Rebuild the profile ColumnCombobox from the current VM profiles tuple."""
        selected_name = self._vm.selected_profile_name_var.get()
        self._profile_combo.clear()
        self._profile_combo.add_items(list(self._vm.profiles))
        for idx, row in enumerate(self._vm.profiles):
            if row.display_name == selected_name:
                self._profile_combo.current(idx)
                break

    # =========================================================================
    # Sync callbacks (View-owned traces)
    # =========================================================================

    def _sync_frame3_state(self, *_: object) -> None:
        """Enable or disable all frame3 interactive widgets based on is_frame3_enabled_var."""
        enabled = self._vm.is_frame3_enabled_var.get()
        state = "normal" if enabled else "disabled"
        for widget in self._frame3_widgets:
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass
        self._profile_combo.set_enabled(enabled)

    def _sync_create_btn(self, *_: object) -> None:
        """Mirror can_create_project_var onto the Create button state."""
        state = "normal" if self._vm.can_create_project_var.get() else "disabled"
        self._create_btn.configure(state=state)

    def _sync_save_project_btn(self, *_: object) -> None:
        """Mirror can_save_project_var onto the Save-project button state."""
        state = "normal" if self._vm.can_save_project_var.get() else "disabled"
        self._save_project_btn.configure(state=state)

    def _sync_save_profile_btn(self, *_: object) -> None:
        """Mirror can_save_profile_var onto the Save-profile button state."""
        state = "normal" if self._vm.can_save_profile_var.get() else "disabled"
        self._save_profile_btn.configure(state=state)

    def _sync_manage_btns(self, *_: object) -> None:
        """Mirror can_manage_project_var onto the Rename and Delete buttons."""
        state = "normal" if self._vm.can_manage_project_var.get() else "disabled"
        self._rename_btn.configure(state=state)
        self._delete_btn.configure(state=state)

    # =========================================================================
    # Event handlers
    # =========================================================================

    def _on_listbox_select(self, _event: object) -> None:
        """Forward the listbox selection to the VM as a select_project action."""
        selection = self._project_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        rows = self._vm.projects
        if idx < len(rows):
            self._vm.select_project(rows[idx].id_project)

    def _on_profile_combo_selected(self, _event: object) -> None:
        """Propagate the ColumnCombobox selection to selected_profile_name_var."""
        obj = self._profile_combo.get_selected_object()
        if obj is not None and isinstance(obj, ProfileRowState):
            self._vm.selected_profile_name_var.set(obj.display_name)

    # =========================================================================
    # Scrollable canvas helpers
    # =========================================================================

    def _on_inner_configure(self, _event: object) -> None:
        """Update the canvas scroll region when the inner frame resizes."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: object) -> None:
        """Stretch the inner frame to fill the canvas width."""
        if hasattr(event, "width"):
            self._canvas.itemconfigure(self._canvas_window, width=event.width)  # type: ignore[union-attr]

    # =========================================================================
    # Teardown
    # =========================================================================

    def teardown(self) -> None:
        """Remove all View-owned traces before the VM is disposed."""
        self._vm.is_frame3_enabled_var.trace_remove("write", self._frame3_trace_id)
        self._vm.can_create_project_var.trace_remove("write", self._can_create_trace_id)
        self._vm.can_save_project_var.trace_remove("write", self._can_save_project_trace_id)
        self._vm.can_save_profile_var.trace_remove("write", self._can_save_profile_trace_id)
        self._vm.can_manage_project_var.trace_remove("write", self._can_manage_trace_id)


# EOF
