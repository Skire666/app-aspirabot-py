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

from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem, StepItem
from views.components.column_combobox.column_combobox import ColumnCombobox
from views.components.folder_link_widget import FolderLinkWidget
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
        """Build all four sections in order."""
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True)
        self._create_scenario_section(outer)
        self._create_profiles_section(outer)
        self._create_profile_config_section(outer)
        self._create_launch_section(outer)

    def _create_scenario_section(self, parent: tk.Widget) -> None:
        """Build the scenario selection section."""
        frame = HorizontalLineFrame(parent, text="Liste des scénarios")
        frame.pack(fill=tk.X)

        self._btn_edit = ttk.Button(frame, text="Modifier", command=self._on_edit_clicked)
        self._btn_edit.pack(side=tk.RIGHT, padx=(0, 5), pady=(0, 5))

        self._btn_refresh = ttk.Button(frame, text="Rafraîchir", command=self._on_refresh_clicked)
        self._btn_refresh.pack(side=tk.RIGHT, padx=(0, 5), pady=(0, 5))

        self._combo_scenarios = ColumnCombobox(frame)
        self._combo_scenarios.add_column("scenario_name", lambda m: m.scenario_name, width=140)
        self._combo_scenarios.add_column("scenario_desc", lambda m: m.scenario_desc, width=200)
        self._combo_scenarios.add_column("id_file", lambda m: m.id_file, width=60)
        self._combo_scenarios.set_display_column("scenario_name")
        self._combo_scenarios.bind("<<ComboboxSelected>>", self._on_combo_scenario_changed)
        self._combo_scenarios.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10), pady=(0, 5))

    def _create_profiles_section(self, parent: tk.Widget) -> None:
        """Build the available-profiles section."""
        frame = HorizontalLineFrame(parent, text="Profils disponibles")
        frame.pack(fill=tk.X)

        self._listbox_profiles = tk.Listbox(frame, height=5, selectmode=tk.SINGLE, exportselection=False)
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

    def _create_profile_config_section(self, parent: tk.Widget) -> None:
        """Build the launch-profile configuration section."""
        self._frame_profile_cfg = HorizontalLineFrame(parent, text="Profil de lancement")
        self._frame_profile_cfg.pack(fill=tk.X)
        container = ttk.Frame(self._frame_profile_cfg)
        container.pack(fill=tk.X)
        self._cfg_grid = container
        self._create_cfg_row0(container)
        self._create_cfg_row1(container)
        self._create_cfg_source_row(container)
        self._create_cfg_panels_container(container)
        self._create_cfg_panel_manual()
        self._create_cfg_panel_folder()
        self._create_cfg_panel_json()
        self._create_cfg_row_warmup(container)
        self._create_cfg_row5(container)
        self._create_cfg_row6(container)

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

        FolderLinkWidget(
            row, title="Dossier", path="Cliquer pour ouvrir", callback=lambda: self._vm.open_export_folder()
        ).pack(side=tk.RIGHT, padx=(0, 10), pady=(0, 5))
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

    def _create_cfg_source_row(self, parent: tk.Widget) -> None:
        """Source-type row — three RadioButtons replacing the old Combobox."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Source d'URL :", width=15).pack(side=tk.LEFT, padx=5, pady=(0, 5))
        for label, value in (
            ("Liste manuelle", UrlSourceTypeEnum.E_MANUAL.value),
            ("Dossier avec URL", UrlSourceTypeEnum.E_FOLDER.value),
            ("Dossier avec JSON", UrlSourceTypeEnum.E_JSON.value),
        ):
            ttk.Radiobutton(
                row,
                text=label,
                variable=self._vm.url_source_type_var,
                value=value,
                command=lambda: self._vm.form_changed(),
            ).pack(side=tk.LEFT, padx=(0, 20), pady=(0, 5))

    def _create_cfg_panels_container(self, parent: tk.Widget) -> None:
        """Create the container that holds the three mode panels (always packed)."""
        self._panels_container = ttk.Frame(parent)
        self._panels_container.pack(fill=tk.X)

    def _create_cfg_panel_manual(self) -> None:
        """MANUAL panel — editable text widget with URL counter."""
        self._panel_manual = ttk.Frame(self._panels_container)

        inner = ttk.Frame(self._panel_manual)
        inner.pack(fill=tk.X)

        left = ttk.Frame(inner)
        left.pack(side=tk.LEFT, anchor=tk.NW, padx=(5, 24), pady=(0, 5))
        ttk.Label(left, text="Aperçu URLs :").pack(anchor=tk.W)
        ttk.Label(left, textvariable=self._vm.url_count_manual_var).pack(anchor=tk.W)

        preview_frame = ttk.Frame(inner)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._txt_url_manual = tk.Text(preview_frame, height=7, wrap=tk.NONE)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_manual.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_manual.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_manual.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))
        self._txt_url_manual.bind("<<Modified>>", self._on_manual_text_modified)

    def _create_cfg_panel_folder(self) -> None:
        """FOLDER panel — path entry, read-only preview, and sort-order RadioButtons."""
        self._panel_folder = ttk.Frame(self._panels_container)
        self._create_folder_path_row(self._panel_folder)
        self._create_folder_preview_row(self._panel_folder)
        self._create_folder_sort_row(self._panel_folder)

    def _create_folder_path_row(self, parent: tk.Widget) -> None:
        """Path entry row with browse button for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Chemin :", width=16).pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
        self._view_traces.append(
            (
                self._vm.url_source_path_shortcuts_var,
                self._vm.url_source_path_shortcuts_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.url_source_path_shortcuts_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(0, 5)
        )
        ttk.Button(row, text="Parcourir", command=self._browse_shortcuts_folder).pack(
            side=tk.RIGHT, padx=(0, 5), pady=(0, 5)
        )

    def _create_folder_preview_row(self, parent: tk.Widget) -> None:
        """Preview row with URL count and scrolled text for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        left = ttk.Frame(row)
        left.pack(side=tk.LEFT, anchor=tk.NW, padx=(5, 24), pady=(0, 5))
        ttk.Label(left, text="Aperçu URLs :").pack(anchor=tk.W)
        ttk.Label(left, textvariable=self._vm.url_count_shortcuts_var).pack(anchor=tk.W)
        preview_frame = ttk.Frame(row)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._txt_url_shortcuts = tk.Text(preview_frame, height=7, wrap=tk.NONE, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_shortcuts.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_shortcuts.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_shortcuts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))

    def _create_folder_sort_row(self, parent: tk.Widget) -> None:
        """Sort-order RadioButtons row for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Ordre de lecture :", width=15).pack(side=tk.LEFT, padx=(105, 5), pady=(0, 5))
        ttk.Radiobutton(
            row,
            text="Lire récemment modifié",
            variable=self._vm.url_sort_order_shortcuts_var,
            value=UrlSortOrderEnum.E_MTIME_DESC.value,
            command=lambda: self._vm.form_changed(),
        ).pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))
        ttk.Radiobutton(
            row,
            text="Lire les plus anciens",
            variable=self._vm.url_sort_order_shortcuts_var,
            value=UrlSortOrderEnum.E_MTIME_ASC.value,
            command=lambda: self._vm.form_changed(),
        ).pack(side=tk.LEFT, pady=(0, 5))

    def _create_cfg_panel_json(self) -> None:
        """JSON panel — path entry, read-only preview, and sort-order RadioButtons."""
        self._panel_json = ttk.Frame(self._panels_container)
        self._create_json_path_row(self._panel_json)
        self._create_json_preview_row(self._panel_json)
        self._create_json_sort_row(self._panel_json)

    def _create_json_path_row(self, parent: tk.Widget) -> None:
        """Path entry row with browse button for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Chemin :", width=16).pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
        self._view_traces.append(
            (
                self._vm.url_source_path_jsons_var,
                self._vm.url_source_path_jsons_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.url_source_path_jsons_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(0, 5)
        )
        ttk.Button(row, text="Parcourir", command=self._browse_jsons_folder).pack(
            side=tk.RIGHT, padx=(0, 5), pady=(0, 5)
        )

    def _create_json_preview_row(self, parent: tk.Widget) -> None:
        """Preview row with URL count and scrolled text for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        left = ttk.Frame(row)
        left.pack(side=tk.LEFT, anchor=tk.NW, padx=(5, 24), pady=(0, 5))
        ttk.Label(left, text="Aperçu URLs :").pack(anchor=tk.W)
        ttk.Label(left, textvariable=self._vm.url_count_jsons_var).pack(anchor=tk.W)
        preview_frame = ttk.Frame(row)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._txt_url_jsons = tk.Text(preview_frame, height=7, wrap=tk.NONE, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_jsons.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_jsons.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_jsons.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))

    def _create_json_sort_row(self, parent: tk.Widget) -> None:
        """Sort-order RadioButtons row for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Ordre de lecture :", width=15).pack(side=tk.LEFT, padx=(105, 5), pady=(0, 5))
        ttk.Radiobutton(
            row,
            text="Lire récemment modifié",
            variable=self._vm.url_sort_order_jsons_var,
            value=UrlSortOrderEnum.E_MTIME_DESC.value,
            command=lambda: self._vm.form_changed(),
        ).pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))
        ttk.Radiobutton(
            row,
            text="Lire les plus anciens",
            variable=self._vm.url_sort_order_jsons_var,
            value=UrlSortOrderEnum.E_MTIME_ASC.value,
            command=lambda: self._vm.form_changed(),
        ).pack(side=tk.LEFT, pady=(0, 5))

    def _create_cfg_row_warmup(self, parent: tk.Widget) -> None:
        """Warmup URL row — optional URL to open before the run starts."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Préchauffe URL : ").pack(side=tk.LEFT, padx=5, pady=(0, 5))
        self._view_traces.append(
            (self._vm.warmup_url_var, self._vm.warmup_url_var.trace_add("write", lambda *_: self._vm.form_changed()))
        )
        ttk.Entry(row, textvariable=self._vm.warmup_url_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(0, 5)
        )

    def _create_cfg_row5(self, parent: tk.Widget) -> None:
        """Row 5 — global error threshold."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Erreurs globales max. avant mise en pause d'urgence :").pack(
            side=tk.LEFT, padx=5, pady=(0, 5)
        )
        self._view_traces.append(
            (
                self._vm.global_threshold_var,
                self._vm.global_threshold_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.global_threshold_var, width=12).pack(side=tk.LEFT, pady=(0, 5))

    def _create_cfg_row6(self, parent: tk.Widget) -> None:
        """Row 6 — per-step error threshold with step selector."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Mettre en pause l'étape :").pack(side=tk.LEFT, padx=5, pady=(0, 5))
        self._combo_steps = ttk.Combobox(row, state="readonly", width=35)
        self._combo_steps.pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
        self._combo_steps.bind("<<ComboboxSelected>>", self._on_step_selected)
        self._view_traces.append(
            (
                self._vm.step_threshold_var,
                self._vm.step_threshold_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Label(row, text=" après  ").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self._vm.step_threshold_var, width=10).pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
        ttk.Label(row, text="erreurs").pack(side=tk.LEFT)

    def _create_launch_section(self, parent: tk.Widget) -> None:
        """Build the launch-trigger section."""
        frame = HorizontalLineFrame(parent, text="Lancer le scraping")
        frame.pack(fill=tk.X)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(row, text="Vérification :").pack(side=tk.LEFT, padx=5, pady=(0, 5))
        ttk.Label(row, textvariable=self._vm.verification_message_var, foreground="red").pack(
            side=tk.LEFT, fill=tk.X, expand=True, pady=(0, 5)
        )

        self._btn_launch = ttk.Button(row, text="Lancer le scraping", width=25, command=lambda: self._vm.launch())
        self._btn_launch.pack(side=tk.RIGHT, padx=(10, 0), pady=(0, 5))

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
            (self._vm.is_manual_panel_visible_var, self._sync_manual_panel),
            (self._vm.is_folder_panel_visible_var, self._sync_folder_panel),
            (self._vm.is_json_panel_visible_var, self._sync_json_panel),
            (self._vm.manual_urls_version_var, self._sync_manual_text),
            (self._vm.url_preview_shortcuts_version_var, self._sync_shortcuts_preview),
            (self._vm.url_preview_jsons_version_var, self._sync_jsons_preview),
        ]
        for var, cb in bindings:
            self._view_traces.append((var, var.trace_add("write", cb)))
        self._apply_initial_state()

    def teardown(self) -> None:
        """Detach all view-owned VM traces and dispose the ViewModel."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()
        self._vm.dispose()

    def _apply_initial_state(self) -> None:
        self._sync_profiles_list_enabled()
        self._sync_profile_section_enabled()
        self._sync_edit_btn()
        self._sync_rename_btn()
        self._sync_delete_btn()
        self._sync_save_btn()
        self._sync_manual_panel()
        self._sync_folder_panel()
        self._sync_json_panel()

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

    def _sync_manual_panel(self, *_: object) -> None:
        """Show or hide the MANUAL mode panel based on is_manual_panel_visible_var."""
        if self._vm.is_manual_panel_visible_var.get():
            self._panel_manual.pack(fill=tk.X)
        else:
            self._panel_manual.pack_forget()

    def _sync_folder_panel(self, *_: object) -> None:
        """Show or hide the FOLDER mode panel based on is_folder_panel_visible_var."""
        if self._vm.is_folder_panel_visible_var.get():
            self._panel_folder.pack(fill=tk.X)
        else:
            self._panel_folder.pack_forget()

    def _sync_json_panel(self, *_: object) -> None:
        """Show or hide the JSON mode panel based on is_json_panel_visible_var."""
        if self._vm.is_json_panel_visible_var.get():
            self._panel_json.pack(fill=tk.X)
        else:
            self._panel_json.pack_forget()

    def _sync_manual_text(self, *_: object) -> None:
        """Repopulate the MANUAL text widget when the Presenter loads a profile."""
        text = self._vm.manual_urls_var.get()
        self._txt_url_manual.configure(state=tk.NORMAL)
        self._txt_url_manual.delete("1.0", tk.END)
        self._txt_url_manual.insert("1.0", text)
        self._txt_url_manual.edit_modified(False)

    def _sync_shortcuts_preview(self, *_: object) -> None:
        """Update the FOLDER read-only text widget from the shortcuts preview list."""
        text = "\n".join(self._vm.get_url_preview_shortcuts())
        self._write_readonly_text(self._txt_url_shortcuts, text)

    def _sync_jsons_preview(self, *_: object) -> None:
        """Update the JSON read-only text widget from the jsons preview list."""
        text = "\n".join(self._vm.get_url_preview_jsons())
        self._write_readonly_text(self._txt_url_jsons, text)

    def _sync_profiles_list_enabled(self, *_: object) -> None:
        """Enable or disable the profile listbox and Nouveau button."""
        state = tk.NORMAL if self._vm.is_profiles_list_enabled_var.get() else tk.DISABLED
        self._listbox_profiles.configure(state=state)
        self._btn_new.configure(state=state)

    def _sync_profile_section_enabled(self, *_: object) -> None:
        """Enable or disable the entire profile-config section."""
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

        _apply(self._cfg_grid)
        if enabled:
            self._sync_manual_panel()
            self._sync_folder_panel()
            self._sync_json_panel()
            # Readonly text widgets must remain disabled even when the section is active.
            self._txt_url_shortcuts.configure(state=tk.DISABLED)
            self._txt_url_jsons.configure(state=tk.DISABLED)
        else:
            self._txt_url_manual.configure(state=tk.DISABLED)
            self._txt_url_shortcuts.configure(state=tk.DISABLED)
            self._txt_url_jsons.configure(state=tk.DISABLED)

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
        self.after(1000, self._reset_refresh_cooldown)
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

    def _on_manual_text_modified(self, _event: tk.Event) -> None:
        if self._txt_url_manual.edit_modified():
            # Tkinter Text sets modified=True once and won't fire <<Modified>> again until it is cleared.
            self._txt_url_manual.edit_modified(False)
            content = self._txt_url_manual.get("1.0", tk.END)
            self._vm.manual_urls_var.set(content)
            self._vm.form_changed()

    def _browse_export_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier d'export", parent=self)
        if folder:
            self._vm.export_folder_var.set(folder)

    def _browse_shortcuts_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier source (URL)", parent=self)
        if folder:
            self._vm.url_source_path_shortcuts_var.set(folder)

    def _browse_jsons_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choisir le dossier source (JSON)", parent=self)
        if folder:
            self._vm.url_source_path_jsons_var.set(folder)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_readonly_text(widget: tk.Text, text: str) -> None:
        """Replace the content of a read-only text widget.

        Args:
            widget: The ``tk.Text`` to update.
            text: New text content to display.
        """
        # DISABLED state makes insert/delete no-ops; temporarily re-enable to update content.
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        # Clear the modified flag so <<Modified>> fires correctly on the next user edit.
        widget.edit_modified(False)
        widget.configure(state=tk.DISABLED)


# EOF
