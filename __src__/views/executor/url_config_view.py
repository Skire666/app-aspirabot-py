"""Tkinter view for the URL source configuration panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk
from typing import Any

from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.i18n_fra import C_DISCOVER_DELETE_CONFIRM_MSG, C_DISCOVER_DELETE_CONFIRM_TITLE
from shared.operating_system_util import open_folder
from view_models.executor_view_model import ExecutorViewModel
from views.components.data_grid.data_grid import DataGrid, GridColumn
from views.components.folder_link_widget import FolderLinkWidget

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_BACKGROUND_GRAY = "#EAEAEA"

_DISCOVER_GRID_COLUMNS: list[GridColumn] = [
    GridColumn(id="dossier", title="Dossier (entrée)", width=200),
    GridColumn(id="fichiers", title="Fichiers (regexp)", width=120),
    GridColumn(id="mapping", title="Clé (Niv. 1)", width=100),
    GridColumn(id="urls", title="URLs", width=100),
    GridColumn(id="action_mod", title="", width=60, col_type="button", button_text="Modif."),
    GridColumn(id="action_del", title="", width=60, col_type="button", button_text="Supp."),
]

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlConfigView(ttk.Frame):
    """Radio-button URL source configuration embedded in the executor panel.

    Sections:
        Radio bar — four mutually exclusive source selectors.
        Panels — one frame per source, shown/hidden via pack/pack_forget.
    """

    def __init__(self, parent: tk.Widget, vm: ExecutorViewModel) -> None:
        """Build the radio bar and bind to ViewModel Vars.

        Args:
            parent: Parent Tkinter container.
            vm: ExecutorViewModel owning all URL configuration state.
        """
        super().__init__(parent)
        self._vm = vm
        self._view_traces: list[tuple[tk.Variable, str]] = []
        # Local var shared by the 4 radio buttons
        self._panel_var = tk.StringVar(master=self, value=UrlSourceTypeEnum.E_MANUAL.value)
        # Currently visible panel; None until first _show_panel call.
        self._current_panel: ttk.Frame | None = None

        self._create_widgets()
        self._bind_vm_vars()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build the radio bar and the four content panels."""
        outer = tk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True)
        self._create_radio_bar(outer)
        self._panels_container = ttk.Frame(outer)
        self._panels_container.pack(fill=tk.BOTH, expand=True)
        self._create_panel_manual()
        self._create_panel_folder()
        self._create_panel_json()
        self._create_panel_discover()

    def _create_radio_bar(self, parent: tk.Widget) -> None:
        """Four radio buttons sharing _panel_var — one per content panel."""
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, padx=4, pady=6)
        self._radio_buttons: list[ttk.Radiobutton] = []
        entries = [
            ("Entrée manuelle", UrlSourceTypeEnum.E_MANUAL.value),
            ("Dossier avec URL", UrlSourceTypeEnum.E_FOLDER.value),
            ("Dossier avec JSON", UrlSourceTypeEnum.E_JSON.value),
            ("Lire les nouveautés", UrlSourceTypeEnum.E_DISCOVER.value),
        ]
        tk.Label(bar, text="Source :").pack(side=tk.LEFT, padx=(0, 10))
        for label, value in entries:
            rb = ttk.Radiobutton(
                bar, text=label, variable=self._panel_var, value=value, command=self._on_panel_var_changed
            )
            rb.pack(side=tk.LEFT, padx=(0, 14))
            self._radio_buttons.append(rb)

    # ─── Panel 1 : Liste manuelle ─────────────────────────────────────────────

    def _create_panel_manual(self) -> None:
        """Panel 1 — editable text widget with URL counter."""
        self._panel_manual = ttk.Frame(self._panels_container)

        # Stats row — packed first so it claims its space before expand kicks in.
        stats = ttk.Frame(self._panel_manual)
        stats.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        ttk.Label(stats, text="Nombre total d'URLs :").pack(side=tk.LEFT, padx=(5, 8))
        ttk.Label(stats, textvariable=self._vm.url_total_count_manual_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Uniques :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_manual_unique_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Doublons :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_manual_dupplicate_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Lignes vides :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_manual_empty_var).pack(side=tk.LEFT)

        # Text area fills the remaining space above the stats row.
        inner = ttk.Frame(self._panel_manual)
        inner.pack(fill=tk.BOTH, expand=True)

        self._txt_url_manual = tk.Text(inner, wrap=tk.NONE)
        scrollbar = ttk.Scrollbar(inner, orient=tk.VERTICAL, command=self._txt_url_manual.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_manual.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_manual.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=(0, 5))
        self._txt_url_manual.bind("<<Modified>>", self._on_manual_text_modified)

    # ─── Panel 2 : Dossier avec URL ──────────────────────────────────────────

    def _create_panel_folder(self) -> None:
        """Panel 2 — folder of .url shortcut files with preview and sort options."""
        self._panel_folder = ttk.Frame(self._panels_container)
        self._create_folder_stats_row(self._panel_folder)
        self._create_folder_path_row(self._panel_folder)
        self._create_folder_sort_row(self._panel_folder)
        self._create_folder_preview_row(self._panel_folder)

    def _create_folder_path_row(self, parent: tk.Widget) -> None:
        """Path entry row with browse button for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Chemin :").pack(side=tk.LEFT, padx=5, pady=(0, 5))
        self._view_traces.append(
            (
                self._vm.url_source_path_shortcuts_var,
                self._vm.url_source_path_shortcuts_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.url_source_path_shortcuts_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(0, 5)
        )
        FolderLinkWidget(row, title="", path="Ouvrir le dossier", callback=self._open_shortcuts_folder).pack(
            side=tk.RIGHT, padx=(0, 10), pady=(0, 5)
        )
        ttk.Button(row, text="...", width=3, command=self._browse_shortcuts_folder).pack(
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
        left.pack(side=tk.LEFT, anchor=tk.NW, pady=6)
        preview_frame = ttk.Frame(row)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._txt_url_shortcuts = tk.Text(preview_frame, wrap=tk.NONE, state=tk.DISABLED, bg=C_BACKGROUND_GRAY)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_shortcuts.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_shortcuts.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_shortcuts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=6)

    def _create_folder_stats_row(self, parent: tk.Widget) -> None:
        """Stats row (total / unique / duplicates / empty) for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        stats = ttk.Frame(parent)
        stats.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        ttk.Label(stats, text="Nombre total d'URLs :").pack(side=tk.LEFT, padx=(5, 8))
        ttk.Label(stats, textvariable=self._vm.url_total_count_shortcuts_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Uniques :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_shortcuts_unique_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Doublons :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_shortcuts_duplicate_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Lignes vides :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_shortcuts_empty_var).pack(side=tk.LEFT)

    def _create_folder_sort_row(self, parent: tk.Widget) -> None:
        """Sort-order RadioButtons row for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Ordre de lecture :", width=15).pack(side=tk.LEFT, padx=5, pady=(0, 5))
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

        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(
            row,
            text="[IMPORTANT] - La date de modification est actualisée après chaque appel à OpenURL... (dès l'ouverture)",
        ).pack(side=tk.LEFT, padx=5, pady=(0, 5))

    # ─── Panel 3 : Dossier avec JSON ─────────────────────────────────────────

    def _create_panel_json(self) -> None:
        """Panel 3 — folder of .json files with preview and sort options."""
        self._panel_json = ttk.Frame(self._panels_container)
        self._create_json_stats_row(self._panel_json)
        self._create_json_path_row(self._panel_json)
        self._create_json_sort_row(self._panel_json)
        self._create_json_preview_row(self._panel_json)

    def _create_json_path_row(self, parent: tk.Widget) -> None:
        """Path entry row with browse button for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Chemin :").pack(side=tk.LEFT, padx=5, pady=(0, 5))
        self._view_traces.append(
            (
                self._vm.url_source_path_jsons_var,
                self._vm.url_source_path_jsons_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        ttk.Entry(row, textvariable=self._vm.url_source_path_jsons_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(0, 5)
        )
        FolderLinkWidget(row, title="", path="Ouvrir le dossier", callback=self._open_shortcuts_json).pack(
            side=tk.RIGHT, padx=(0, 10), pady=(0, 5)
        )
        ttk.Button(row, text="...", width=3, command=self._browse_jsons_folder).pack(
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
        left.pack(side=tk.LEFT, anchor=tk.NW, pady=6)
        preview_frame = ttk.Frame(row)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._txt_url_jsons = tk.Text(preview_frame, wrap=tk.NONE, state=tk.DISABLED, bg=C_BACKGROUND_GRAY)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_jsons.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_jsons.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_jsons.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=6)

    def _create_json_stats_row(self, parent: tk.Widget) -> None:
        """Stats row (total / unique / duplicates / empty) for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        stats = ttk.Frame(parent)
        stats.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        ttk.Label(stats, text="Nombre total d'URLs :").pack(side=tk.LEFT, padx=(5, 8))
        ttk.Label(stats, textvariable=self._vm.url_total_count_jsons_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Uniques :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_jsons_unique_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Doublons :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_jsons_duplicate_var).pack(side=tk.LEFT, padx=(0, 50))
        ttk.Label(stats, text="Lignes vides :").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(stats, textvariable=self._vm.url_count_jsons_empty_var).pack(side=tk.LEFT)

    def _create_json_sort_row(self, parent: tk.Widget) -> None:
        """Sort-order RadioButtons row for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Ordre de lecture :", width=15).pack(side=tk.LEFT, padx=5, pady=(0, 5))
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

    # ─── Panel 4 : Découverte automatique ────────────────────────────────────

    def _create_panel_discover(self) -> None:
        """Panel 4 — IN grid, IN/OUT forms, and compute row for URL discovery."""
        self._panel_discover = ttk.Frame(self._panels_container)
        self._create_discover_toolbar(self._panel_discover)
        self._create_discover_compute_row(self._panel_discover)
        self._create_discover_out_section(self._panel_discover)
        self._create_discover_grid(self._panel_discover)

    def _create_discover_toolbar(self, parent: tk.Widget) -> None:
        """Toolbar row with the [IN] add button above the discover grid.

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=4, pady=(4, 2))
        ttk.Button(row, text="+ Ajouter une source [IN]", command=self._on_add_discover_click).pack(side=tk.LEFT)

    def _open_discover_popup(self) -> None:
        """Open the modal [IN] Source dialog for creating or modifying a discover entry."""
        size_h, size_w = 190, 600
        popup = tk.Toplevel(self)
        popup.title("Source [IN]")
        popup.resizable(False, False)
        popup.geometry(f"{size_w}x{size_h}")
        popup.grab_set()

        frame = ttk.LabelFrame(popup, text="Champs")
        frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        def browse_in_folder() -> None:
            folder = filedialog.askdirectory(title="Choisir le dossier [IN] source", parent=popup)
            if folder:
                self._vm.disc_in_folder_var.set(folder)

        def make_row(label: str, var: tk.StringVar, browse_cb: Callable[[], None] | None = None) -> None:
            r = ttk.Frame(frame)
            r.pack(fill=tk.X, padx=4, pady=2)
            ttk.Label(r, text=label, width=18, anchor=tk.W).pack(side=tk.LEFT)
            ttk.Entry(r, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
            if browse_cb:
                ttk.Button(r, text="...", width=3, command=browse_cb).pack(side=tk.LEFT)

        # create popup lines
        make_row("Dossier d'entrée :", self._vm.disc_in_folder_var, browse_cb=browse_in_folder)
        make_row("Fichiers (regexp) :", self._vm.disc_in_pattern_json_var)
        make_row("Clé (Niv 1) :", self._vm.disc_in_key_mapping_var)
        make_row("URLs (regexp) :", self._vm.disc_in_pattern_urls_var)

        btn_row = ttk.Frame(popup)
        btn_row.pack(fill=tk.X, padx=8, pady=(4, 8))

        can_create = self._vm.can_create_discover_var.get()
        can_modify = self._vm.can_modify_discover_var.get()

        def do_create() -> None:
            self._vm.add_discover()
            self._vm.form_changed()
            popup.destroy()

        def do_modify() -> None:
            self._vm.update_discover()
            self._vm.form_changed()
            popup.destroy()

        ttk.Button(btn_row, text="Créer", command=do_create, state=tk.NORMAL if can_create else tk.DISABLED).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btn_row, text="Modifier", command=do_modify, state=tk.NORMAL if can_modify else tk.DISABLED).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btn_row, text="Annuler", command=popup.destroy).pack(side=tk.LEFT)

        popup.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - popup.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")

    def _make_discover_field_row(
        self,
        parent: tk.Widget,
        label: str,
        var: tk.StringVar,
        browse: bool = False,
        browse_cb: Callable[[], None] | None = None,
    ) -> ttk.Entry:
        """Build one Label + Entry (+ optional browse button) row.

        Also registers a form_changed trace on the var.

        Args:
            parent: Container frame to pack into.
            label: Text for the left-side label.
            var: StringVar to bind to the entry.
            browse: When True, adds a "…" browse button.
            browse_cb: Callback invoked by the browse button.

        Returns:
            The created Entry widget.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(row, text=label, width=12, anchor=tk.W).pack(side=tk.LEFT)
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        if browse and browse_cb:
            ttk.Button(row, text="...", width=3, command=browse_cb).pack(side=tk.LEFT)
        self._view_traces.append((var, var.trace_add("write", lambda *_: self._vm.form_changed())))
        return entry

    def _create_discover_grid(self, parent: tk.Widget) -> None:
        """DataGrid [IN]: Modifier / Supprimer action buttons per row.

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        self._grid_discover = DataGrid(parent, columns=_DISCOVER_GRID_COLUMNS, on_action=self._on_discover_action)
        self._grid_discover.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

    def _create_discover_out_section(self, parent: tk.Widget) -> None:
        """[OUT] form with 4 fields (reference — already-processed URLs).

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        frame = tk.Frame(parent)
        frame.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=(2, 2))
        ttk.Label(frame, text="Fichiers de sorties :").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Entry(frame, textvariable=self._vm.disc_out_pattern_json_var, width=25).pack(side=tk.LEFT, padx=(0, 25))
        ttk.Label(frame, text="Clé (Niv. 1) :").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Entry(frame, textvariable=self._vm.disc_out_key_mapping_var, width=15).pack(side=tk.LEFT, padx=(0, 25))
        ttk.Label(frame, text="URLs (regexp) :").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Entry(frame, textvariable=self._vm.disc_out_pattern_urls_var, width=15).pack(side=tk.LEFT)

    def _create_discover_compute_row(self, parent: tk.Widget) -> None:
        """Compute button and verification status label.

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=(4, 6))
        ttk.Button(row, text="Calculer la liste", command=self._vm.compute_discovers).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(row, textvariable=self._vm.discover_compute_message_var).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # ViewModel bindings
    # ------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace listeners and perform the initial sync."""
        bindings: list[tuple[tk.Variable, Callable[..., object]]] = [
            (self._vm.manual_urls_version_var, self._sync_manual_text),
            (self._vm.url_preview_shortcuts_version_var, self._sync_shortcuts_preview),
            (self._vm.url_preview_jsons_version_var, self._sync_jsons_preview),
            (self._vm.url_source_type_var, self._sync_panel_from_vm),
            (self._vm.is_profile_section_active_var, self._sync_section_enabled),
            (self._vm.discovers_in_version_var, self._sync_discovers_grid),
        ]
        for var, cb in bindings:
            self._view_traces.append((var, var.trace_add("write", cb)))
        self._sync_panel_from_vm()
        self._sync_section_enabled()

    # ------------------------------------------------------------------
    # Sync methods (called by trace_add)
    # ------------------------------------------------------------------

    def _sync_panel_from_vm(self, *_: object) -> None:
        """Sync the active panel and radio selection to url_source_type_var."""
        stype = self._vm.url_source_type_var.get()
        if stype not in {
            UrlSourceTypeEnum.E_MANUAL.value,
            UrlSourceTypeEnum.E_FOLDER.value,
            UrlSourceTypeEnum.E_JSON.value,
            UrlSourceTypeEnum.E_DISCOVER.value,
        }:
            return
        # Programmatic .set() does NOT fire command= on radio buttons — no feedback loop.
        self._panel_var.set(stype)
        self._show_panel(stype)

    def _sync_manual_text(self, *_: object) -> None:
        """Repopulate the manual text widget when the Presenter loads a profile."""
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

    def _sync_discovers_grid(self, *_: object) -> None:
        """Rebuild the [IN] DataGrid from the current discovers rows snapshot."""
        rows = self._vm.get_discovers_in_rows()
        data = [
            {
                "dossier": r.folder_json,
                "fichiers": r.pattern_json,
                "mapping": r.key_mapping,
                "urls": r.pattern_urls,
                "__bound__": r.id_discover,
            }
            for r in rows
        ]
        self._grid_discover.render_data(data)

    def _on_add_discover_click(self) -> None:
        """Reset the IN form to create-mode then open the popup."""
        self._vm.prepare_new_discover()
        self._open_discover_popup()

    def _sync_section_enabled(self, *_: object) -> None:
        """Enable or disable URL config widgets based on is_profile_section_active_var."""
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

        _apply(self)
        # Readonly preview widgets must stay disabled even when the section is active.
        if enabled:
            self._txt_url_shortcuts.configure(state=tk.DISABLED)
            self._txt_url_jsons.configure(state=tk.DISABLED)
        else:
            self._txt_url_manual.configure(state=tk.DISABLED)
            self._txt_url_shortcuts.configure(state=tk.DISABLED)
            self._txt_url_jsons.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_panel_var_changed(self) -> None:
        """React to user radio-button click; switch panel and notify VM."""
        val = self._panel_var.get()
        self._show_panel(val)
        self._vm.url_source_type_var.set(val)
        self._vm.form_changed()

    def _on_manual_text_modified(self, _event: tk.Event) -> None:
        """Propagate manual-URL edits to the ViewModel and notify form changed."""
        if self._txt_url_manual.edit_modified():
            self._txt_url_manual.edit_modified(False)
            content = self._txt_url_manual.get("1.0", tk.END)
            self._vm.manual_urls_var.set(content)
            self._vm.form_changed()

    def _on_discover_action(self, action_id: str, bound: object) -> None:
        """Handle Modifier / Supprimer actions from the [IN] DataGrid.

        Args:
            action_id: "action_mod" or "action_del".
            bound: The id_discover string from the row's __bound__.
        """
        id_discover = str(bound)
        if action_id == "action_mod":
            self._vm.select_discover(id_discover)
            self._open_discover_popup()
        elif action_id == "action_del":
            if messagebox.askyesno(
                title=C_DISCOVER_DELETE_CONFIRM_TITLE, message=C_DISCOVER_DELETE_CONFIRM_MSG, parent=self
            ):
                self._vm.delete_discover(id_discover)

    def _browse_shortcuts_folder(self) -> None:
        """Open a folder dialog and write the result to url_source_path_shortcuts_var."""
        folder = filedialog.askdirectory(title="Choisir le dossier source (URL)", parent=self)
        if folder:
            self._vm.url_source_path_shortcuts_var.set(folder)

    def _open_shortcuts_folder(self) -> None:
        """Open the shortcuts folder in the OS file explorer."""
        path = self._vm.url_source_path_shortcuts_var.get()
        if path:
            open_folder(path)

    def _browse_jsons_folder(self) -> None:
        """Open a folder dialog and write the result to url_source_path_jsons_var."""
        folder = filedialog.askdirectory(title="Choisir le dossier source (JSON)", parent=self)
        if folder:
            self._vm.url_source_path_jsons_var.set(folder)

    def _open_shortcuts_json(self) -> None:
        """Open the shortcuts folder in the OS file explorer."""
        path = self._vm.url_source_path_jsons_var.get()
        if path:
            open_folder(path)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def teardown(self) -> None:
        """Detach all view-owned traces to prevent memory leaks when the view is destroyed."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _show_panel(self, key: str) -> None:
        """Hide the current panel and display the one matching ``key``.

        Args:
            key: A UrlSourceTypeEnum value.
        """
        panel_map: dict[str, ttk.Frame] = {
            UrlSourceTypeEnum.E_MANUAL.value: self._panel_manual,
            UrlSourceTypeEnum.E_FOLDER.value: self._panel_folder,
            UrlSourceTypeEnum.E_JSON.value: self._panel_json,
            UrlSourceTypeEnum.E_DISCOVER.value: self._panel_discover,
        }
        target = panel_map.get(key)
        if target is None or target is self._current_panel:
            return
        if self._current_panel is not None:
            self._current_panel.pack_forget()
        target.pack(fill=tk.BOTH, expand=True)
        self._current_panel = target

    @staticmethod
    def _write_readonly_text(widget: tk.Text, text: str) -> None:
        """Replace the content of a read-only text widget.

        Args:
            widget: The ``tk.Text`` to update.
            text: New text content to display.
        """
        # DISABLED makes insert/delete no-ops; re-enable temporarily to update.
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.edit_modified(False)
        widget.configure(state=tk.DISABLED)


# EOF
