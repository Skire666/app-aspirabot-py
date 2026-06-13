"""Tkinter view for the URL source configuration panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, ttk
from typing import Any

from shared.app_global_state import MyButton, MyEntry, MyLabel
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.operating_system_util import open_folder
from view_models.executor_view_model import ExecutorViewModel
from views.components.editable_table.editable_table import ActionColumnDef, EditableTable, TableConfig, TextColumnDef
from views.components.folder_link_widget import FolderLinkWidget

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_BACKGROUND_GRAY = "#EAEAEA"


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
        bar.pack(fill=tk.X)
        self._radio_buttons: list[ttk.Radiobutton] = []
        entries = [
            ("Entrée manuelle", UrlSourceTypeEnum.E_MANUAL.value),
            ("Dossier avec URL", UrlSourceTypeEnum.E_FOLDER.value),
            ("Dossier avec JSON", UrlSourceTypeEnum.E_JSON.value),
            ("Lire les nouveautés", UrlSourceTypeEnum.E_DISCOVER.value),
        ]
        MyLabel(bar, text="Source :").pack_left()
        for label, value in entries:
            rb = ttk.Radiobutton(
                bar, text=label, variable=self._panel_var, value=value, command=self._on_panel_var_changed
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))
            self._radio_buttons.append(rb)

    # ─── Panel 1 : Liste manuelle ─────────────────────────────────────────────

    def _create_panel_manual(self) -> None:
        """Panel 1 — editable text widget with URL counter."""
        self._panel_manual = ttk.Frame(self._panels_container)

        # Stats row — packed first so it claims its space before expand kicks in.
        stats = ttk.Frame(self._panel_manual)
        stats.pack(side=tk.BOTTOM, fill=tk.X)
        MyLabel(stats, text="Nombre total d'URLs :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_total_count_manual_var, width=10).pack_left()
        MyLabel(stats, text="Uniques :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_manual_unique_var, width=10).pack_left()
        MyLabel(stats, text="Doublons :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_manual_dupplicate_var, width=10).pack_left()
        MyLabel(stats, text="Lignes vides :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_manual_empty_var, width=10).pack_left()

        # Text area fills the remaining space above the stats row.
        inner = ttk.Frame(self._panel_manual)
        inner.pack(fill=tk.BOTH, expand=True)

        self._txt_url_manual = tk.Text(inner, wrap=tk.NONE)
        scrollbar = ttk.Scrollbar(inner, orient=tk.VERTICAL, command=self._txt_url_manual.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_manual.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_manual.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)
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
        MyLabel(row, text="Chemin :").pack_left()
        self._view_traces.append(
            (
                self._vm.url_source_path_shortcuts_var,
                self._vm.url_source_path_shortcuts_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        MyEntry(row, textvariable=self._vm.url_source_path_shortcuts_var).pack_left(fill=tk.X, expand=True)
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
        self._txt_url_shortcuts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)

    def _create_folder_stats_row(self, parent: tk.Widget) -> None:
        """Stats row (total / unique / duplicates / empty) for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        stats = ttk.Frame(parent)
        stats.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        MyLabel(stats, text="Nombre total d'URLs :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_total_count_shortcuts_var, width=10).pack_left()
        MyLabel(stats, text="Uniques :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_shortcuts_unique_var, width=10).pack_left()
        MyLabel(stats, text="Doublons :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_shortcuts_duplicate_var, width=10).pack_left()
        MyLabel(stats, text="Lignes vides :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_shortcuts_empty_var, width=10).pack_left()

    def _create_folder_sort_row(self, parent: tk.Widget) -> None:
        """Sort-order RadioButtons row for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        MyLabel(row, text="Ordre de lecture :", width=15).pack_left()
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
        MyLabel(
            row,
            text="[IMPORTANT] - La date de modification est actualisée après chaque appel à OpenURL... (dès l'ouverture)",
        ).pack_left()

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
        self._txt_url_jsons.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)

    def _create_json_stats_row(self, parent: tk.Widget) -> None:
        """Stats row (total / unique / duplicates / empty) for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        stats = ttk.Frame(parent)
        stats.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        MyLabel(stats, text="Nombre total d'URLs :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_total_count_jsons_var, width=10).pack_left()
        MyLabel(stats, text="Uniques :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_jsons_unique_var, width=10).pack_left()
        MyLabel(stats, text="Doublons :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_jsons_duplicate_var, width=10).pack_left()
        MyLabel(stats, text="Lignes vides :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_jsons_empty_var, width=10).pack_left()

    def _create_json_sort_row(self, parent: tk.Widget) -> None:
        """Sort-order RadioButtons row for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        MyLabel(row, text="Ordre de lecture :", width=15).pack_left()
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
        self._create_discover_compute_row(self._panel_discover)
        self._create_discover_out_section(self._panel_discover)
        self._create_discover_grid(self._panel_discover)

    def _create_discover_grid(self, parent: tk.Widget) -> None:
        """EditableTable [IN]: Modifier action button per row; built-in delete delegates to VM.

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        config = TableConfig(
            columns=[
                TextColumnDef(key="col_dossier", header="Dossier (entrée)", width=180, editable=True, sortable=True),
                ActionColumnDef(
                    key="action_browse",
                    header="📂 ...",
                    width=50,
                    label="📂 ...",
                    target_key="col_dossier",
                    handler=self._on_discover_browse_action,
                ),
                TextColumnDef(key="col_fichiers", header="Fichiers (regexp)", width=120, editable=True, sortable=True),
                TextColumnDef(key="col_mapping", header="Clé (Niv. 1)", width=100, editable=True, sortable=True),
                TextColumnDef(key="col_urls", header="URLs (regexp)", width=100, editable=True, sortable=True),
            ],
            confirm_delete=True,
            on_change=self._on_discover_table_change,
        )
        self._grid_discover = EditableTable(parent, config=config)
        self._grid_discover.pack(fill=tk.BOTH, expand=True)

    def _create_discover_out_section(self, parent: tk.Widget) -> None:
        """[OUT] form with 4 fields (reference — already-processed URLs).

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        frame = tk.Frame(parent)
        frame.pack(side=tk.BOTTOM, fill=tk.X)
        for var in (
            self._vm.disc_out_pattern_json_var,
            self._vm.disc_out_key_mapping_var,
            self._vm.disc_out_pattern_urls_var,
        ):
            self._view_traces.append((var, var.trace_add("write", lambda *_: self._vm.form_changed())))
        MyLabel(frame, text="Fichiers de sorties :").pack_left()
        MyEntry(frame, textvariable=self._vm.disc_out_pattern_json_var, width=25).pack_left()
        MyLabel(frame, text="Clé (Niv. 1) :").pack_left()
        MyEntry(frame, textvariable=self._vm.disc_out_key_mapping_var, width=15).pack_left()
        MyLabel(frame, text="URLs (regexp) :").pack_left()
        MyEntry(frame, textvariable=self._vm.disc_out_pattern_urls_var, width=15).pack_left()

    def _create_discover_compute_row(self, parent: tk.Widget) -> None:
        """Compute button and verification status label.

        Args:
            parent: The DISCOVER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.BOTTOM, fill=tk.X)
        MyButton(row, text="Calculer la liste", command=self._vm.compute_discovers).pack_left()
        MyLabel(row, textvariable=self._vm.discover_compute_message_var).pack_left()

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
        """Rebuild the [IN] EditableTable from the current discovers rows snapshot."""
        rows = self._vm.get_discovers_in_rows()
        data = [
            {
                "col_dossier": r.folder_json,
                "col_fichiers": r.pattern_json,
                "col_mapping": r.key_mapping,
                "col_urls": r.pattern_urls,
                "__bound__": str(r.id_discover),
            }
            for r in rows
        ]
        self._grid_discover.set_data(data)

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

    def _on_discover_table_change(self, rows: list[dict[str, str]]) -> None:
        """Keep VM discover rows in sync with the EditableTable on every mutation.

        Called by EditableTable.on_change after any inline edit, deletion, or
        clear. Updates the VM silently (no version bump) so that the Presenter
        can read the current state without triggering a table reload loop.

        Args:
            rows: Full rows_data snapshot after the mutation.
        """
        self._vm.update_discovers_table_state(rows)

    def _on_discover_browse_action(self, _row_idx: int, _row_data: dict[str, str]) -> str | None:
        """Open a folder dialog and return the selected path to populate col_dossier.

        The returned value is written to ``col_dossier`` by the EditableTable
        ``target_key`` mechanism.

        Args:
            _row_idx: Zero-based row index (unused).
            _row_data: Current row dict (unused).
        """
        folder = filedialog.askdirectory(title="Choisir le dossier [IN] source", parent=self)
        return folder or None

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
