"""Panel for configuring the export folder, URL source, and auto-export option."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from views.components.canvas_checkbox import CanvasCheckbox
from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Radio button value tokens for URL source selection.
_URL_SOURCE_MANUAL = "manual"
_URL_SOURCE_FOLDER = "folder"
_URL_SOURCE_CSV = "csv"

# Emergency stop threshold bounds.
_C_EMERGENCY_STOP_MIN = 1
_C_EMERGENCY_STOP_MAX = 9_999_999

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_state_recursive(widget: tk.Widget, state: str) -> None:
    """Recursively apply a Tkinter state to a widget and all its children.

    Args:
        widget: Root widget to start from.
        state: ``"normal"`` or ``"disabled"``.
    """
    with contextlib.suppress(tk.TclError):
        widget.configure(state=state)
    for child in widget.winfo_children():
        _apply_state_recursive(child, state)


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class LaunchProfilePanel(ttk.Frame):
    """Panel for the launch profile: export folder, URL source, and auto-export.

    Example:
        >>> panel = LaunchProfilePanel(config_model, parent)
        >>> panel.set_on_form_changed(lambda: print("changed"))
    """

    def __init__(self, config_model: AppConfigurationModel, parent: tk.Widget) -> None:
        """Initialize the panel and build widgets.

        Args:
            config_model: Application configuration providing the default export folder.
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_form_changed_cb: Callable[[], None] | None = None
        self._on_manual_urls_confirmed_cb: Callable[[str], None] | None = None
        self._on_open_export_folder_cb: Callable[[], None] | None = None

        # URL-source state — empty until the user picks a source.
        self._url_source_type: str = ""
        self._url_source_value: list[str] | str | None = None

        # Suppresses the StringVar trace during programmatic set_export_folder() calls.
        self._suppress_form_changed: bool = False

        self._app_config_model = config_model
        self._export_folder: str = str((Path.cwd() / config_model.folder_scraping).resolve())
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build and pack the four configuration rows."""
        self._frame = HorizontalLineFrame(self, text="Profil de lancement")
        self._frame.pack(side=tk.TOP, fill=tk.X)

        # Export folder row.
        self._build_export_folder_row(self._frame)

        # URL source radio row.
        self._build_url_source_row(self._frame)

        # Source detail display row.
        self._build_source_detail_row(self._frame)

        # Auto-export checkbox row.
        self._build_auto_export_row(self._frame)

        # Emergency stop threshold row.
        self._build_emergency_stop_row(self._frame)

    def _build_export_folder_row(self, parent: tk.Frame) -> None:
        """Build the export-folder selector row.

        Args:
            parent: Container frame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        ttk.Label(row, text="Dossier d'export :").pack(side=tk.LEFT, padx=5)

        # StringVar keeps the Entry field in sync with internal state.
        self._var_export_folder = tk.StringVar(value=self._export_folder)
        self._var_export_folder.trace_add("write", self._on_export_folder_var_changed)
        ttk.Entry(row, textvariable=self._var_export_folder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row, text="Parcourir", command=self._browse_export_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Ouvrir dossier", command=self._open_export_folder).pack(side=tk.LEFT, padx=(5, 5))

    def _build_url_source_row(self, parent: tk.Frame) -> None:
        """Build the URL-source radio-button row.

        Args:
            parent: Container frame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        ttk.Label(row, text="Source des URLs :").pack(side=tk.LEFT, padx=(5))

        # StringVar tracks the active radio selection.
        self._var_url_source = tk.StringVar()
        self._var_url_source.set(None)
        radio_defs = [
            ("Depuis une liste", _URL_SOURCE_MANUAL),
            ("Depuis un dossier", _URL_SOURCE_FOLDER),
            ("Depuis un fichier CSV", _URL_SOURCE_CSV),
        ]
        for label, value in radio_defs:
            ttk.Radiobutton(
                row,
                text=label,
                variable=self._var_url_source,
                value=value,
                command=lambda v=value: self._on_url_source_changed(v),
            ).pack(side=tk.LEFT, padx=(5), pady=(0, 5))

    def _build_source_detail_row(self, parent: tk.Frame) -> None:
        """Build the read-only source-detail row displayed below the radio buttons.

        Args:
            parent: Container frame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        ttk.Label(row, text="Détails source :").pack(side=tk.LEFT, padx=(5))

        # Read-only entry reflecting the active source value.
        self._var_source_detail = tk.StringVar()
        self._detail_entry = ttk.Entry(row, textvariable=self._var_source_detail, state="readonly")
        self._detail_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    def _build_auto_export_row(self, parent: tk.Frame) -> None:
        """Build the auto-export journal checkbox row.

        Args:
            parent: Container frame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X)

        self._var_auto_export_journal = tk.BooleanVar(value=True)
        CanvasCheckbox(
            row,
            text="Exporter journal scraping nt à la fin du processus",
            variable=self._var_auto_export_journal,
        ).pack(side=tk.LEFT, padx=5, pady=(5))

    def _build_emergency_stop_row(self, parent: tk.Frame) -> None:
        """Build the emergency stop threshold label and Spinbox row.

        Args:
            parent: Container frame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=(2, 4))

        ttk.Label(row, text="Mettre en pause automatiquement après X erreurs :").pack(side=tk.LEFT, padx=5)

        # StringVar allows trace-based change detection and text validation.
        self._var_emergency_stop = tk.StringVar(value="10")
        self._var_emergency_stop.trace_add("write", self._on_emergency_stop_threshold_changed)
        ttk.Spinbox(
            row,
            from_=_C_EMERGENCY_STOP_MIN,
            to=_C_EMERGENCY_STOP_MAX,
            textvariable=self._var_emergency_stop,
            width=10,
        ).pack(side=tk.LEFT, padx=(0, 5))

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_on_form_changed(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user modifies the launch profile form.

        Args:
            callback: Zero-argument callable notified on every user-driven change.
        """
        self._on_form_changed_cb = callback

    def set_on_manual_urls_confirmed(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user confirms manual URLs.

        Args:
            callback: Callable receiving the raw multiline text entered by the user.
        """
        self._on_manual_urls_confirmed_cb = callback

    def set_on_open_export_folder(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks 'Ouvrir dossier'.

        Args:
            callback: Zero-argument callable that creates the folder and opens it.
        """
        self._on_open_export_folder_cb = callback

    # ------------------------------------------------------------------
    # Public data feed
    # ------------------------------------------------------------------

    def set_export_folder(self, folder: str) -> None:
        """Set the export folder entry and internal state without notifying.

        Args:
            folder: Absolute path to apply to the export folder field.
        """
        self._export_folder = folder
        self._suppress_form_changed = True
        self._var_export_folder.set(folder)
        self._suppress_form_changed = False

    def set_url_source(self, source_type: str, source_value: list[str] | str | None) -> None:
        """Restore the URL source radio selection and internal value.

        Args:
            source_type: One of ``"manual"``, ``"folder"``, ``"csv"``, or ``""``.
            source_value: Matching value — list of URLs, a path string, or None.
        """
        self._url_source_type = source_type
        self._url_source_value = source_value
        self._var_url_source.set(source_type if source_type else "")
        self._refresh_source_detail()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all widgets in the panel.

        Args:
            enabled: True to make the panel interactive; False to gray it out.
        """
        _apply_state_recursive(self._frame, tk.NORMAL if enabled else tk.DISABLED)
        # Keep the detail entry always read-only when the panel is enabled.
        self._detail_entry.configure(state="readonly" if enabled else tk.DISABLED)

    # ------------------------------------------------------------------
    # Public getters
    # ------------------------------------------------------------------

    def get_export_folder(self) -> str:
        """Return the currently selected export folder path.

        Returns:
            str: Absolute path of the selected export folder.
        """
        return self._export_folder

    def get_url_source(self) -> dict[str, Any]:
        """Return the selected URL source type and its collected value.

        Returns:
            Dict with keys ``type`` (``"manual"``, ``"folder"``, or ``"csv"``)
            and ``value`` (list of URL strings or a path string).
        """
        return {"type": self._url_source_type, "value": self._url_source_value}

    def get_auto_export_journal(self) -> bool:
        """Return whether the auto-export journal checkbox is checked.

        Returns:
            bool: True when the journal should be exported automatically.
        """
        return bool(self._var_auto_export_journal.get())

    def get_emergency_stop_threshold(self) -> int | None:
        """Return the emergency stop threshold, or None when the value is invalid.

        Returns:
            int | None: A valid threshold between 1 and 9999999, or None.
        """
        raw = self._var_emergency_stop.get().strip()
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            return None
        else:
            return value if _C_EMERGENCY_STOP_MIN <= value <= _C_EMERGENCY_STOP_MAX else None

    def set_emergency_stop_threshold(self, value: int) -> None:
        """Set the emergency stop Spinbox to the given value without notifying.

        Args:
            value: Threshold to display (must be between 1 and 9999999).
        """
        # Suppress the form-changed notification during programmatic updates.
        self._suppress_form_changed = True
        self._var_emergency_stop.set(str(value))
        self._suppress_form_changed = False

    # ------------------------------------------------------------------
    # URL-source and folder dialogs
    # ------------------------------------------------------------------

    def _on_url_source_changed(self, source_type: str) -> None:
        """Open the appropriate dialog when the user switches URL source.

        Args:
            source_type: One of ``"manual"``, ``"folder"``, or ``"csv"``.
        """
        if source_type == _URL_SOURCE_MANUAL:
            self._collect_manual_urls()
        elif source_type == _URL_SOURCE_FOLDER:
            self._collect_folder_source()
        elif source_type == _URL_SOURCE_CSV:
            self._collect_csv_source()

    def _collect_manual_urls(self) -> None:
        """Open a popup for the user to paste a newline-separated URL list."""
        popup = tk.Toplevel(self)
        popup.title("Saisir les URLs")
        popup.grab_set()

        ttk.Label(popup, text="Collez les URLs (une par ligne) :").pack(padx=10, pady=(10, 4))

        # Multiline text area for URL input.
        text = tk.Text(popup, width=60, height=12)
        text.pack(padx=10, pady=(0, 6))

        # Pre-fill with existing manual URLs if any.
        if isinstance(self._url_source_value, list):
            text.insert(tk.END, "\n".join(self._url_source_value))

        self._build_manual_url_buttons(popup, text)

    def _build_manual_url_buttons(self, popup: tk.Toplevel, text: tk.Text) -> None:
        """Add OK / Annuler buttons to the manual-URL popup.

        Args:
            popup: The Toplevel dialog to attach the buttons to.
            text: The Text widget whose content is passed to the confirmed callback.
        """

        def _on_ok() -> None:
            # Pass raw text to the presenter; it handles parsing and filtering.
            raw = text.get("1.0", tk.END)
            popup.destroy()
            if self._on_manual_urls_confirmed_cb:
                self._on_manual_urls_confirmed_cb(raw)

        def _on_cancel() -> None:
            self._var_url_source.set(self._url_source_type)
            popup.destroy()

        btn_frame = ttk.Frame(popup)
        btn_frame.pack(pady=(0, 10))
        ttk.Button(btn_frame, text="OK", command=_on_ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Annuler", command=_on_cancel).pack(side=tk.LEFT, padx=6)

    def _collect_folder_source(self) -> None:
        """Open a folder dialog to set the URL source directory."""
        folder = filedialog.askdirectory(title="Sélectionner le dossier source des URLs")
        if folder:
            self._url_source_type = _URL_SOURCE_FOLDER
            self._url_source_value = folder
            self._refresh_source_detail()
            self._notify_form_changed()
        else:
            # Revert radio to the previous source type on cancel.
            self._var_url_source.set(self._url_source_type)

    def _collect_csv_source(self) -> None:
        """Open a file dialog to select a CSV file as the URL source."""
        path = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
        )
        if path:
            self._url_source_type = _URL_SOURCE_CSV
            self._url_source_value = path
            self._refresh_source_detail()
            self._notify_form_changed()
        else:
            # Revert radio to the previous source type on cancel.
            self._var_url_source.set(self._url_source_type)

    def _browse_export_folder(self) -> None:
        """Open a folder dialog to select the export destination."""
        folder = filedialog.askdirectory(
            title="Sélectionner le dossier d'export",
            initialdir=self._export_folder,
        )
        if folder:
            self._export_folder = folder
            self._var_export_folder.set(folder)
            self._notify_form_changed()

    def _open_export_folder(self) -> None:
        """Notify the presenter to create the export folder and open it."""
        if self._on_open_export_folder_cb:
            self._on_open_export_folder_cb()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_source_detail(self) -> None:
        """Update the source-detail entry to reflect the current URL source state."""
        if self._url_source_type == _URL_SOURCE_MANUAL:
            # Show first URL from the list, or a placeholder when the list is empty.
            urls = self._url_source_value if isinstance(self._url_source_value, list) else []
            text = urls[0] if urls else "(aucune URL renseignée)"
        elif self._url_source_type in {_URL_SOURCE_FOLDER, _URL_SOURCE_CSV}:
            # Show the selected path, or a placeholder when none was chosen.
            path = self._url_source_value if isinstance(self._url_source_value, str) else ""
            text = path if path else "(aucun chemin renseigné)"
        else:
            text = ""
        self._var_source_detail.set(text)

    def _on_export_folder_var_changed(self, *_: str) -> None:
        """Fired by the StringVar trace when the export folder Entry changes.

        Args:
            *_: Tkinter trace arguments (name, index, mode) — unused.
        """
        if self._suppress_form_changed:
            return
        self._export_folder = self._var_export_folder.get()
        self._notify_form_changed()

    def _on_emergency_stop_threshold_changed(self, *_: str) -> None:
        """Fired by the StringVar trace when the emergency stop Spinbox changes.

        Args:
            *_: Tkinter trace arguments (name, index, mode) — unused.
        """
        if self._suppress_form_changed:
            return
        self._notify_form_changed()

    def _notify_form_changed(self) -> None:
        """Notify the presenter that the user has modified the launch form."""
        if self._on_form_changed_cb:
            self._on_form_changed_cb()


# EOF
