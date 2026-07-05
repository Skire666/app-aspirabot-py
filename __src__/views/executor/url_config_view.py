"""Tkinter view for the URL source configuration panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, ttk
from typing import Any

from shared.app_global_state import MyButton, MyCombobox, MyEntry, MyLabel, MyRadioButton
from shared.constants import C_COLUMN_DATE_CREATED, C_COLUMN_DATE_MODIFIED, C_COLUMN_DATE_SESSION
from shared.enums import RelativeDateEnum, UrlSortOrderEnum, UrlSourceTypeEnum
from shared.operating_system_util import open_folder
from view_models.executor_view_model import ExecutorViewModel
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
        self._panel_var = tk.StringVar(master=self, value=UrlSourceTypeEnum.E_MANUAL_LIST.value)
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

    def _create_radio_bar(self, parent: tk.Widget) -> None:
        """Four radio buttons sharing _panel_var — one per content panel."""
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X)
        self._radio_buttons: list[ttk.Radiobutton] = []
        entries = [
            ("Saisie manuelle", UrlSourceTypeEnum.E_MANUAL_LIST.value),
            ("Dossier avec '.url'", UrlSourceTypeEnum.E_FOLDER_RACS.value),
            ("Dossier avec '.csv'", UrlSourceTypeEnum.E_REFRESH_URLS.value),
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
        MyLabel(stats, textvariable=self._vm.url_count_manual_duplicate_var, width=10).pack_left()
        MyLabel(stats, text="Lignes vides :").pack_left()
        MyLabel(stats, textvariable=self._vm.url_count_manual_empty_var, width=10).pack_left()

        # Text area fills the remaining space above the stats row.
        inner = ttk.Frame(self._panel_manual)
        inner.pack(fill=tk.BOTH, expand=True, pady=5)

        self._txt_url_manual = tk.Text(inner, wrap=tk.NONE)
        scrollbar = ttk.Scrollbar(inner, orient=tk.VERTICAL, command=self._txt_url_manual.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_manual.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_manual.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
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
        MyLabel(row, text="Dossier avec '.url' :").pack_left()
        self._view_traces.append(
            (
                self._vm.urls_path_folder_racs_var,
                self._vm.urls_path_folder_racs_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        MyEntry(row, textvariable=self._vm.urls_path_folder_racs_var).pack_left(fill=tk.X, expand=True)
        FolderLinkWidget(row, title="", path="Ouvrir le dossier", callback=self._open_shortcuts_folder).pack(
            side=tk.RIGHT, padx=(0, 10), pady=(0, 5)
        )
        MyButton(row, text="...", width=3, command=self._browse_shortcuts_folder).pack_right()

    def _create_folder_preview_row(self, parent: tk.Widget) -> None:
        """Preview row with URL count and scrolled text for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        left = ttk.Frame(row)
        left.pack(side=tk.LEFT, anchor=tk.NW)
        preview_frame = ttk.Frame(row)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        self._txt_url_shortcuts = tk.Text(preview_frame, wrap=tk.NONE, state=tk.DISABLED, bg=C_BACKGROUND_GRAY)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_shortcuts.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_shortcuts.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_shortcuts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_folder_stats_row(self, parent: tk.Widget) -> None:
        """Stats row (total / unique / duplicates / empty) for the FOLDER source panel.

        Args:
            parent: The FOLDER panel frame to attach widgets to.
        """
        stats = ttk.Frame(parent)
        stats.pack(side=tk.BOTTOM, fill=tk.X)
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
        MyRadioButton(
            row,
            text="Lire récents en 1er",
            variable=self._vm.url_sort_order_shortcuts_var,
            value=UrlSortOrderEnum.E_NEWEST_FIRST.value,
            command=lambda: self._vm.form_changed(),
        ).pack_left()
        MyRadioButton(
            row,
            text="Lire anciens en 1er",
            variable=self._vm.url_sort_order_shortcuts_var,
            value=UrlSortOrderEnum.E_OLDEST_FIRST.value,
            command=lambda: self._vm.form_changed(),
        ).pack_left()

        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        MyLabel(
            row,
            text=(
                "[IMPORTANT] - La date de modification est actualisée après chaque appel à OpenURL... (dès l'ouverture)"
            ),
        ).pack_left()

    # ─── Panel 3 : Dossier avec JSON ─────────────────────────────────────────

    def _create_panel_json(self) -> None:
        """Panel 3 — folder of .json files with preview and sort options."""
        self._panel_json = ttk.Frame(self._panels_container)
        self._create_json_stats_row(self._panel_json)
        self._create_json_path_row(self._panel_json)
        self._create_json_dates_between(self._panel_json)
        self._create_json_sort_row(self._panel_json)
        self._create_json_preview_row(self._panel_json)

    def _create_json_path_row(self, parent: tk.Widget) -> None:
        """Path entry row with browse button for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        MyLabel(row, text="Chemin vers fichier CSV :").pack_left()
        self._view_traces.append(
            (
                self._vm.urls_path_folder_csv_var,
                self._vm.urls_path_folder_csv_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )
        MyEntry(row, textvariable=self._vm.urls_path_folder_csv_var).pack_left(fill=tk.X, expand=True)
        FolderLinkWidget(row, title="", path="Ouvrir le dossier", callback=self._open_folder_csv).pack(
            side=tk.RIGHT, padx=(0, 10), pady=(0, 5)
        )
        MyButton(row, text="...", width=3, command=self._browse_csvs_file).pack_right()

    def _create_json_preview_row(self, parent: tk.Widget) -> None:
        """Preview row with URL count and scrolled text for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        left = ttk.Frame(row)
        left.pack(side=tk.LEFT, anchor=tk.NW)
        preview_frame = ttk.Frame(row)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        self._txt_url_jsons = tk.Text(preview_frame, wrap=tk.NONE, state=tk.DISABLED, bg=C_BACKGROUND_GRAY)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._txt_url_jsons.yview)  # type: ignore[reportUnknownMemberType]
        self._txt_url_jsons.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._txt_url_jsons.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_json_stats_row(self, parent: tk.Widget) -> None:
        """Stats row (total / unique / duplicates / empty) for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        stats = ttk.Frame(parent)
        stats.pack(side=tk.BOTTOM, fill=tk.X)
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
        MyRadioButton(
            row,
            text="Lire récents en 1er",
            variable=self._vm.url_sort_order_csv_var,
            value=UrlSortOrderEnum.E_NEWEST_FIRST.value,
            command=lambda: self._vm.form_changed(),
        ).pack_left()
        MyRadioButton(
            row,
            text="Lire anciens en 1er",
            variable=self._vm.url_sort_order_csv_var,
            value=UrlSortOrderEnum.E_OLDEST_FIRST.value,
            command=lambda: self._vm.form_changed(),
        ).pack_left()
        MyRadioButton(
            row,
            text="Lire prioritaires en 1er",
            variable=self._vm.url_sort_order_csv_var,
            value=UrlSortOrderEnum.E_PRIORITY_FIRST.value,
            command=lambda: self._vm.form_changed(),
        ).pack_left()

    def _create_json_dates_between(self, parent: tk.Widget) -> None:
        """Date-range filter row for the JSON source panel.

        Args:
            parent: The JSON panel frame to attach widgets to.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        values_coloumn = [C_COLUMN_DATE_CREATED, C_COLUMN_DATE_MODIFIED, C_COLUMN_DATE_SESSION]
        MyLabel(row, text="Filtrer : ").pack_left()
        self._add_bound_combobox(row, self._vm.csv_date_type_used_var, values_coloumn, width=18)
        date_values = [e.enum_to_view() for e in RelativeDateEnum if e.is_valid()]
        MyLabel(row, text=" entre ").pack_left()
        self._add_bound_combobox(row, self._vm.csv_date_start_var, date_values, width=12)
        MyLabel(row, text="et").pack_left()
        self._add_bound_combobox(row, self._vm.csv_date_end_var, date_values, width=12)
        MyEntry(row, textvariable=self._vm.url_x_top_csv_var, width=6).pack_right()
        MyLabel(row, text="Limiter nombre d'URL :").pack_right()
        self._view_traces.append(
            (
                self._vm.url_x_top_csv_var,
                self._vm.url_x_top_csv_var.trace_add("write", lambda *_: self._vm.form_changed()),
            )
        )

    def _add_bound_combobox(self, parent: tk.Widget, var: tk.StringVar, values: list[str], width: int) -> None:
        """Create a readonly combobox bound to *var* and register its form-changed trace.

        Args:
            parent: Widget to attach the combobox to.
            var: StringVar the combobox reads and writes.
            values: Allowed combobox values.
            width: Width of the combobox in characters.
        """
        MyCombobox(parent, textvariable=var, values=values, state="readonly", width=width, height=15).pack_left()
        self._view_traces.append((var, var.trace_add("write", lambda *_: self._vm.form_changed())))

    # ─── Panel 4 : Découverte automatique ────────────────────────────────────

    # ------------------------------------------------------------------
    # ViewModel bindings
    # ------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace listeners and perform the initial sync."""
        bindings: list[tuple[tk.Variable, Callable[..., object]]] = [
            (self._vm.manual_urls_version_var, self._sync_manual_text),
            (self._vm.url_preview_shortcuts_version_var, self._sync_shortcuts_preview),
            (self._vm.url_preview_jsons_version_var, self._sync_jsons_preview),
            (self._vm.urls_source_type_var, self._sync_panel_from_vm),
            (self._vm.is_profile_section_active_var, self._sync_section_enabled),
        ]
        for var, cb in bindings:
            self._view_traces.append((var, var.trace_add("write", cb)))
        self._sync_panel_from_vm()
        self._sync_section_enabled()

    # ------------------------------------------------------------------
    # Sync methods (called by trace_add)
    # ------------------------------------------------------------------

    def _sync_panel_from_vm(self, *_: object) -> None:
        """Sync the active panel and radio selection to urls_source_type_var."""
        stype = self._vm.urls_source_type_var.get()
        if stype not in {
            UrlSourceTypeEnum.E_MANUAL_LIST.value,
            UrlSourceTypeEnum.E_FOLDER_RACS.value,
            UrlSourceTypeEnum.E_REFRESH_URLS.value,
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
        self._vm.urls_source_type_var.set(val)
        self._vm.form_changed()

    def _on_manual_text_modified(self, _event: tk.Event) -> None:
        """Propagate manual-URL edits to the ViewModel and notify form changed."""
        if self._txt_url_manual.edit_modified():
            self._txt_url_manual.edit_modified(False)
            content = self._txt_url_manual.get("1.0", tk.END)
            self._vm.manual_urls_var.set(content)
            self._vm.form_changed()

    def _browse_shortcuts_folder(self) -> None:
        """Open a folder dialog and write the result to urls_path_folder_racs_var."""
        folder = filedialog.askdirectory(title="Choisir le dossier source (URL)", parent=self)
        if folder:
            self._vm.urls_path_folder_racs_var.set(folder)

    def _open_shortcuts_folder(self) -> None:
        """Open the shortcuts folder in the OS file explorer."""
        path = self._vm.urls_path_folder_racs_var.get()
        if path:
            open_folder(path)

    def _browse_csvs_file(self) -> None:
        """Open a folder dialog and write the result to urls_path_folder_csv_var."""
        file = filedialog.askopenfilename(
            title="Choisir le fichier CSV", filetypes=[("CSV Files", "*.csv")], parent=self
        )
        if file:
            self._vm.urls_path_folder_csv_var.set(file)

    def _open_folder_csv(self) -> None:
        """Open the shortcuts folder in the OS file explorer."""
        path = self._vm.urls_path_folder_csv_var.get()
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
            UrlSourceTypeEnum.E_MANUAL_LIST.value: self._panel_manual,
            UrlSourceTypeEnum.E_FOLDER_RACS.value: self._panel_folder,
            UrlSourceTypeEnum.E_REFRESH_URLS.value: self._panel_json,
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
