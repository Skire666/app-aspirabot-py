"""Tkinter panel for monitoring and controlling a live scraping workflow.

Five stacked LabelFrame sections provide: provider selection, launch profile,
workflow controls, live progression, and a step-by-step scraping journal.
All background-thread mutations are deferred to the main thread via
self.after(0, ...). The elapsed timer refreshes every second via
self.after(1000, ...).

Example:
    >>> panel = ScrapingView(content_area)
    >>> panel.set_on_launch(lambda: print("launch"))
    >>> panel.reset()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import contextlib
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from shared.i18n_fra import C_VIEW_SCRAPING_HEADINGS
from shared.operating_system_util import open_folder
from views.components.horizontal_line_frame import HorizontalLineFrame

from __src__.views.components.canvas_checkbox import CanvasCheckbox

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Labels for the three URL-source radio buttons.
_URL_SOURCE_MANUAL = "manual"
_URL_SOURCE_FOLDER = "folder"
_URL_SOURCE_CSV = "csv"

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ScrapingView(ttk.Frame):
    """Scraping panel composed of five vertically stacked frames.

    Section order (top to bottom):
    1. Provider selection dropdown.
    2. Launch profile (export folder + URL source).
    3. Workflow controls (Lancer / Annuler / Pause / Reprendre).
    4. Live progression (7 StringVar fields + elapsed timer).
    5. Scraping journal (Treeview + Export button).
    """

    def __init__(self, config_model: AppConfigurationModel, parent: tk.Widget) -> None:
        """Initialize the scraping panel and build all widgets.

        Args:
            parent: The parent Tkinter widget (e.g. main_view.content_area).
        """
        super().__init__(parent)

        # Callback slots — populated by the presenter via set_on_*().
        self._on_launch: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_pause: Callable[[], None] | None = None
        self._on_resume: Callable[[], None] | None = None
        self._on_provider_selected: Callable[[str], None] | None = None
        self._on_refresh_providers: Callable[[], None] | None = None
        self._on_export_journal: Callable[[str], None] | None = None
        self._on_profile_selected_cb: Callable[[str], None] | None = None
        self._on_profile_new_cb: Callable[[str], None] | None = None
        self._on_profile_save_cb: Callable[[], None] | None = None
        self._on_profile_delete_cb: Callable[[str], None] | None = None
        self._on_form_changed_cb: Callable[[], None] | None = None

        # Profile list — parallel to the Listbox entries.
        self._profile_ids: list[str] = []

        # Provider id_file index — maps combobox values to id_file strings.
        self._provider_id_by_display: dict[str, str] = {}

        # URL-source state — None until the user explicitly picks a source.
        self._url_source_type: str = ""
        self._url_source_value: list[str] | str | None = None

        # Suppresses the _var_export_folder trace during programmatic set_export_folder() calls.
        self._suppress_form_changed: bool = False

        # Export folder path.
        self._app_config_model = config_model
        self._export_folder: str = None

        # Elapsed timer state.
        self._elapsed_timer_id: str | None = None
        self._run_started_at: datetime | None = None

        self._create_widgets()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build and pack all section frames."""
        self._create_provider_selection_frame()
        self._create_profile_management_frame()
        self._create_launch_profile_frame()
        self._create_workflow_controls_frame()
        self._create_journal_frame()

    def _create_provider_selection_frame(self) -> None:
        """Build the 'Sélectionner un fournisseur' section."""
        frame = HorizontalLineFrame(self, text="Sélectionner un fournisseur")
        frame.pack(side=tk.TOP, fill=tk.X)

        # Combobox shows "Name — URL — Version — modified_date".
        self._cmb_provider = ttk.Combobox(frame, state="readonly", width=80)
        self._cmb_provider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self._cmb_provider.bind("<<ComboboxSelected>>", self._on_combobox_selected)

        # Refresh button reloads the provider list from disk.
        btn_refresh = ttk.Button(frame, text="Rafraîchir", command=self._notify_refresh_providers)
        btn_refresh.pack(side=tk.RIGHT, padx=5)

    def _create_profile_management_frame(self) -> None:
        """Build the 'Gestion des profils' section."""
        self._frame_profile_management = HorizontalLineFrame(self, text="Gestion des profils")
        self._frame_profile_management.pack(side=tk.TOP, fill=tk.X)

        # Left column: profile listbox with scrollbar.
        left = ttk.Frame(self._frame_profile_management)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_profiles_listbox(left)

        # Right column: action buttons stacked vertically.
        right = ttk.Frame(self._frame_profile_management)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        self._create_profiles_buttons(right)

        # Gray out until a provider is loaded.
        self._apply_state_recursive(self._frame_profile_management, tk.DISABLED)

    def _create_profiles_listbox(self, parent: ttk.Frame) -> None:
        """Build the profile Listbox with scrollbar inside the management frame.

        Args:
            parent: Container frame for the listbox column.
        """
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        self._lst_profiles = tk.Listbox(
            parent,
            height=3,
            exportselection=False,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self._lst_profiles.yview)
        self._lst_profiles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._lst_profiles.bind("<<ListboxSelect>>", self._on_profile_listbox_selected)

    def _create_profiles_buttons(self, parent: ttk.Frame) -> None:
        """Build action buttons inside the profile management frame.

        Args:
            parent: Container frame for the button column.
        """
        ttk.Button(parent, text="Nouveau profil", command=self._notify_profile_new, width=18).pack(
            side=tk.TOP, pady=(0, 4), padx=5
        )

        # Store reference so the presenter can control its enabled state.
        self._btn_save_profile = ttk.Button(
            parent, text="Sauvegarder profil", command=self._notify_profile_save, width=18
        )
        self._btn_save_profile.pack(side=tk.TOP, pady=(0, 4), padx=5)

        ttk.Button(parent, text="Supprimer profil", command=self._notify_profile_delete, width=18).pack(
            side=tk.TOP, padx=5
        )

    def _create_launch_profile_frame(self) -> None:
        """Build the 'Profil de lancement' section."""
        # Store reference so the frame can be enabled/disabled as a whole.
        self._frame_launch_profile = HorizontalLineFrame(self, text="Profil de lancement")
        self._frame_launch_profile.pack(side=tk.TOP, fill=tk.X)

        self._create_export_folder_row(self._frame_launch_profile)
        self._create_url_source_row(self._frame_launch_profile)
        self._create_auto_export_row(self._frame_launch_profile)

    def _create_export_folder_row(self, parent: ttk.LabelFrame) -> None:
        """Build the export-folder selector row inside the launch profile frame.

        Args:
            parent: The launch-profile LabelFrame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        ttk.Label(row, text="Dossier d'export :").pack(side=tk.LEFT, padx=5)

        # StringVar keeps the displayed path in sync with internal state.
        self._export_folder = str((Path.cwd() / self._app_config_model.folder_scraping).resolve())

        self._var_export_folder = tk.StringVar(value=self._export_folder)
        self._var_export_folder.trace_add("write", self._on_export_folder_var_changed)
        ttk.Entry(row, textvariable=self._var_export_folder, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(row, text="Parcourir", command=self._browse_export_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Ouvrir dossier", command=self._open_export_folder).pack(side=tk.LEFT, padx=(5, 5))

    def _create_url_source_row(self, parent: ttk.LabelFrame) -> None:
        """Build the URL-source radio-button row inside the launch profile frame.

        Args:
            parent: The launch-profile LabelFrame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        ttk.Label(row, text="URLs à scraper :").pack(side=tk.LEFT, padx=(5, 8))

        # StringVar tracks the active radio selection.
        self._var_url_source = tk.StringVar()
        self._var_url_source.set(None)
        radio_defs = [
            ("Saisie manuelle", _URL_SOURCE_MANUAL),
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
            ).pack(side=tk.LEFT, padx=(0, 12))

    def _create_auto_export_row(self, parent: ttk.LabelFrame) -> None:
        """Build the auto-export journal checkbox row.

        Args:
            parent: The launch-profile LabelFrame to pack into.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X)

        self._var_auto_export_journal = tk.BooleanVar(value=True)
        export = CanvasCheckbox(
            row,
            text="Exporter le journal scraping automatiquement à la fin du processus",
            variable=self._var_auto_export_journal,
        )
        export.pack(side=tk.LEFT, padx=5, pady=(2, 0))

    def _create_workflow_controls_frame(self) -> None:
        """Build the 'Progression' section with 7 live-updated info rows."""
        frame = HorizontalLineFrame(self, text="Pilotage du scraping")
        frame.pack(side=tk.TOP, fill=tk.X)

        frame_stats = ttk.Frame(frame)
        frame_stats.pack(side=tk.LEFT, fill=tk.X)

        # Build StringVars for each field, stored for external updates.
        self._var_prog_url = tk.StringVar(value="—")
        self._var_prog_tabs = tk.StringVar(value="—")
        self._var_prog_step = tk.StringVar(value="—")
        self._var_prog_last_result = tk.StringVar(value="—")
        self._var_prog_status = tk.StringVar(value="inactif")
        self._var_prog_elapsed = tk.StringVar(value="—")
        self._var_prog_stats = tk.StringVar(value="—")

        # Map each label to its StringVar for compact row construction.
        rows_def = [
            ("URL courante :", self._var_prog_url),
            ("Onglets ouverts :", self._var_prog_tabs),
            ("Étape en cours :", self._var_prog_step),
            ("Dernier résultat :", self._var_prog_last_result),
            ("État :", self._var_prog_status),
            ("Démarré / Écoulé :", self._var_prog_elapsed),
            ("Statistiques :", self._var_prog_stats),
        ]
        for label_text, var in rows_def:
            self._add_progress_row(frame_stats, label_text, var)

        # buttson
        div_buttons = ttk.Frame(frame)
        div_buttons.pack(side=tk.RIGHT, fill=tk.X)

        self._btn_launch = ttk.Button(
            div_buttons, text="Lancer le scraping", width=20, command=self._notify_launch
        )
        self._btn_launch.pack(side=tk.TOP, padx=5, pady=(0, 5))

        self._btn_cancel = ttk.Button(
            div_buttons, text="Annuler (kill)", command=self._notify_cancel, width=20, state=tk.DISABLED
        )
        self._btn_cancel.pack(side=tk.TOP, padx=5, pady=(0, 5))

        self._btn_pause = ttk.Button(
            div_buttons, text="Mettre en pause", command=self._notify_pause, width=20, state=tk.DISABLED
        )
        self._btn_pause.pack(side=tk.TOP, padx=5, pady=(0, 5))

        self._btn_resume = ttk.Button(
            div_buttons, text="Reprendre", command=self._notify_resume, width=20, state=tk.DISABLED
        )
        self._btn_resume.pack(side=tk.TOP, padx=5)

    @staticmethod
    def _add_progress_row(parent: ttk.LabelFrame, label_text: str, var: tk.StringVar) -> None:
        """Pack a single label + value row into the progression frame.

        Args:
            parent: The progression LabelFrame.
            label_text: Fixed description label on the left.
            var: StringVar whose value is displayed on the right.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=1, padx=5)
        ttk.Label(row, text=label_text, width=20, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Label(row, textvariable=var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_journal_frame(self) -> None:
        """Build the 'Journal scraping' section with a Treeview and Export button."""
        frame = HorizontalLineFrame(self, text="Journal du scraping")
        frame.pack(side=tk.TOP, fill=tk.BOTH)

        # Top bar: export button aligned right.
        bar = ttk.Frame(frame)
        bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        # Treeview with vertical scrollbar.
        columns = ("date", "step_started", "duration", "success", "msg_step_ended")
        self._tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)

        for col, (title, width, anchor, stretch) in C_VIEW_SCRAPING_HEADINGS.items():
            self._tree.heading(col, text=title)
            self._tree.column(col, width=width, anchor=anchor, stretch=stretch)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

    # ------------------------------------------------------------------
    # Callback registration (called once by the presenter)
    # ------------------------------------------------------------------

    def set_on_launch(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Lancer.

        Args:
            callback: Zero-argument callable that starts the workflow.
        """
        self._on_launch = callback

    def set_on_cancel(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Annuler.

        Args:
            callback: Zero-argument callable that signals cancellation.
        """
        self._on_cancel = callback

    def set_on_pause(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Pause.

        Args:
            callback: Zero-argument callable that pauses the workflow.
        """
        self._on_pause = callback

    def set_on_resume(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Reprendre.

        Args:
            callback: Zero-argument callable that resumes the workflow.
        """
        self._on_resume = callback

    def set_on_provider_selected(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user selects a provider.

        Args:
            callback: Callable receiving the selected provider's id_file.
        """
        self._on_provider_selected = callback

    def set_on_refresh_providers(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Rafraîchir.

        Args:
            callback: Zero-argument callable that reloads the provider list.
        """
        self._on_refresh_providers = callback

    def set_on_export_journal(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user confirms a journal export.

        Args:
            callback: Callable receiving the chosen destination file path.
        """
        self._on_export_journal = callback

    def set_on_profile_selected(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user selects a profile.

        Args:
            callback: Callable receiving the selected profile_id.
        """
        self._on_profile_selected_cb = callback

    def set_on_profile_new(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user confirms a new profile name.

        Args:
            callback: Callable receiving the profile name entered by the user.
        """
        self._on_profile_new_cb = callback

    def set_on_profile_save(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Sauvegarder profil.

        Args:
            callback: Zero-argument callable that persists the current form.
        """
        self._on_profile_save_cb = callback

    def set_on_form_changed(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user modifies the launch profile form.

        Args:
            callback: Zero-argument callable notified on every user-driven change.
        """
        self._on_form_changed_cb = callback

    def set_on_profile_delete(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user deletes a profile.

        Args:
            callback: Callable receiving the profile_id to remove.
        """
        self._on_profile_delete_cb = callback

    # ------------------------------------------------------------------
    # Public data feed (called by the presenter)
    # ------------------------------------------------------------------

    def render_providers_list(self, providers: list[dict[str, Any]]) -> None:
        """Populate the provider combobox with the given provider rows.

        Args:
            providers: List of dicts with keys ``id_file``, ``provider_name``,
                ``url``, ``version``, ``modified_date``.
        """
        self._provider_id_by_display.clear()
        values = []
        for p in providers:
            display = f"{p['provider_name']}  —  {p['url']}  —  v{p['version']}  —  {p['modified_date']}"
            self._provider_id_by_display[display] = p["id_file"]
            values.append(display)

        self._cmb_provider["values"] = values

    def set_selected_provider(self, id_file: str) -> None:
        """Highlight the combobox entry matching id_file.

        Args:
            id_file: The unique provider file identifier to select.
        """
        # Find the display key that maps to the given id_file.
        for display, fid in self._provider_id_by_display.items():
            if fid == id_file:
                self._cmb_provider.set(display)
                return

    def render_profiles_list(self, profiles: list[dict[str, Any]]) -> None:
        """Populate the profile Listbox with the given profile rows.

        Args:
            profiles: List of dicts with keys ``profile_id`` and ``name``.
        """
        self._lst_profiles.delete(0, tk.END)
        self._profile_ids = []

        # Insert each profile name and store the parallel id list.
        for p in profiles:
            self._lst_profiles.insert(tk.END, p["name"])
            self._profile_ids.append(p["profile_id"])

        # Gray out the launch profile section when no profiles exist.
        if not profiles:
            self.set_launch_profile_enabled(False)
            self.set_save_profile_button_state(False)

    def get_selected_profile_id(self) -> str | None:
        """Return the profile_id of the highlighted Listbox entry.

        Returns:
            str | None: The profile_id of the selected entry, or None.
        """
        sel = self._lst_profiles.curselection()
        if not sel:
            return None

        idx = sel[0]
        return self._profile_ids[idx] if idx < len(self._profile_ids) else None

    def set_selected_profile(self, profile_id: str) -> None:
        """Highlight the Listbox entry matching profile_id.

        Args:
            profile_id: The profile identifier to select.
        """
        for idx, pid in enumerate(self._profile_ids):
            if pid == profile_id:
                self._lst_profiles.selection_clear(0, tk.END)
                self._lst_profiles.selection_set(idx)
                self._lst_profiles.see(idx)
                return

    def set_export_folder(self, folder: str) -> None:
        """Set the export folder entry and internal state.

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
            source_type: One of "manual", "folder", "csv", or "".
            source_value: Matching value — list of URLs, a path string, or None.
        """
        self._url_source_type = source_type
        self._url_source_value = source_value
        self._var_url_source.set(source_type if source_type else "")

    def set_profile_management_enabled(self, enabled: bool) -> None:
        """Enable or disable all widgets inside the 'Gestion des profils' frame.

        Args:
            enabled: True to make the frame interactive; False to gray it out.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self._apply_state_recursive(self._frame_profile_management, state)

    def set_launch_profile_enabled(self, enabled: bool) -> None:
        """Enable or disable all widgets inside the 'Profil de lancement' frame.

        Args:
            enabled: True to make the frame interactive; False to gray it out.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self._apply_state_recursive(self._frame_launch_profile, state)

    def set_save_profile_button_state(self, enabled: bool) -> None:
        """Enable or disable the 'Sauvegarder profil' button.

        Args:
            enabled: True when the form has unsaved changes.
        """
        self._btn_save_profile.config(state=tk.NORMAL if enabled else tk.DISABLED)

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

    # ------------------------------------------------------------------
    # Public state management (main thread — called by presenter)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset run-specific UI elements to their initial idle state.

        Clears the progression fields and the journal Treeview. Restores
        all buttons to idle. Must be called from the main thread.
        """
        # Reset all progression StringVars to their placeholder values.
        self._var_prog_url.set("—")
        self._var_prog_tabs.set("—")
        self._var_prog_step.set("—")
        self._var_prog_last_result.set("—")
        self._var_prog_status.set("inactif")
        self._var_prog_elapsed.set("—")
        self._var_prog_stats.set("—")

        # Clear all journal rows.
        self._tree.delete(*self._tree.get_children())

        # Restore all buttons to idle state.
        self._btn_launch.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._btn_pause.config(state=tk.DISABLED)
        self._btn_resume.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Thread-safe render interface
    # ------------------------------------------------------------------

    def set_running_state(self, running: bool) -> None:
        """Toggle button states to match whether a workflow is in progress.

        Safe to call from a background thread.

        Args:
            running: True while the workflow is running; False when idle.
        """
        self.after(0, lambda: self._apply_running_state(running))

    def _apply_running_state(self, running: bool) -> None:
        """Apply button enable/disable state on the main thread.

        Args:
            running: True for running state; False for idle state.
        """
        launch_state = tk.DISABLED if running else tk.NORMAL
        cancel_state = tk.NORMAL if running else tk.DISABLED
        pause_state = tk.NORMAL if running else tk.DISABLED

        self._btn_launch.config(state=launch_state)
        self._btn_cancel.config(state=cancel_state)
        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=tk.DISABLED)

    def set_paused_state(self, paused: bool) -> None:
        """Toggle Pause/Reprendre buttons to match the paused state.

        Safe to call from a background thread.

        Args:
            paused: True while the workflow is paused; False when running.
        """
        self.after(0, lambda: self._apply_paused_state(paused))

    def _apply_paused_state(self, paused: bool) -> None:
        """Apply Pause/Reprendre button states on the main thread.

        Args:
            paused: True to show paused state; False to restore running state.
        """
        pause_state = tk.DISABLED if paused else tk.NORMAL
        resume_state = tk.NORMAL if paused else tk.DISABLED

        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=resume_state)

    def update_progress(
        self,
        url: str,
        tabs: int,
        current_step: str,
        last_result: str,
        status: str,
        stats: dict[str, int],
    ) -> None:
        """Push live progress values to the progression frame.

        Safe to call from a background thread.

        Args:
            url: Current browser page URL.
            tabs: Number of open browser tabs.
            current_step: Label of the step currently executing.
            last_result: Short result string from the last completed step.
            status: Workflow status label (e.g. ``"en cours"``, ``"terminé"``).
            stats: Dict with int values for ``success``, ``errors``,
                ``clicks``, and ``urls``.
        """
        self.after(
            0,
            lambda: self._apply_progress(url, tabs, current_step, last_result, status, stats),
        )

    def _apply_progress(
        self,
        url: str,
        tabs: int,
        current_step: str,
        last_result: str,
        status: str,
        stats: dict[str, int],
    ) -> None:
        """Update progression StringVars on the main thread.

        Args:
            url: Current browser URL.
            tabs: Open tab count.
            current_step: Current step label.
            last_result: Last step result string.
            status: Workflow status string.
            stats: Counters dict (success, errors, clicks, urls).
        """
        self._var_prog_url.set(url or "—")
        self._var_prog_tabs.set(str(tabs) if tabs else "—")
        self._var_prog_step.set(current_step or "—")
        self._var_prog_last_result.set(last_result or "—")
        self._var_prog_status.set(status or "—")

        # Format the statistics line.
        stats_text = (
            f"Succès : {stats.get('success', 0)}  |  "
            f"Erreurs : {stats.get('errors', 0)}  |  "
            f"Clics : {stats.get('clicks', 0)}  |  "
            f"URLs : {stats.get('urls', 0)}"
        )
        self._var_prog_stats.set(stats_text)

    def start_elapsed_timer(self, started_at: datetime) -> None:
        """Start the elapsed-time ticker in the progression frame.

        Safe to call from a background thread — schedules via self.after().

        Args:
            started_at: The datetime at which the workflow started.
        """
        self._run_started_at = started_at
        self.after(0, self._tick_elapsed_timer)

    def stop_elapsed_timer(self) -> None:
        """Cancel the elapsed-time ticker.

        Safe to call from a background thread.
        """
        self.after(0, self._cancel_elapsed_timer)

    def _tick_elapsed_timer(self) -> None:
        """Update the elapsed-time StringVar and reschedule for the next second."""
        if self._run_started_at is None:
            return

        elapsed = datetime.now() - self._run_started_at
        total_s = int(elapsed.total_seconds())
        hours, remainder = divmod(total_s, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format: "HH:MM:SS | démarré à HH:MM:SS"
        start_str = self._run_started_at.strftime("%H:%M:%S")
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self._var_prog_elapsed.set(f"Démarré à {start_str}  |  Écoulé : {elapsed_str}")

        # Schedule next tick and store the ID for cancellation.
        self._elapsed_timer_id = self.after(1000, self._tick_elapsed_timer)

    def _cancel_elapsed_timer(self) -> None:
        """Cancel any pending elapsed-timer callback on the main thread."""
        if self._elapsed_timer_id is not None:
            self.after_cancel(self._elapsed_timer_id)
            self._elapsed_timer_id = None
        self._run_started_at = None

    def start_journal_entry(self, item_id: str, date: str, step_started: str) -> None:
        """Insert a pending journal row before the step executes.

        The row shows the step type immediately with placeholder values in the
        result columns. Call ``complete_journal_entry`` after execution to fill them.
        Safe to call from a background thread.

        Args:
            item_id: Unique Treeview iid used to update the row later.
            date: Timestamp string captured at step start.
            step_started: Step type label (e.g. ``"OPEN_URL"``).
        """
        self.after(0, lambda: self._insert_pending_journal_row(item_id, date, step_started))

    def _insert_pending_journal_row(self, item_id: str, date: str, step_started: str) -> None:
        """Insert a pending row with the given iid on the main thread.

        Args:
            item_id: Treeview iid for the new row.
            date: Timestamp at step start.
            step_started: Step type label.
        """
        # TODO PCO : ordre des colonnes pas explicite
        values = (date, step_started, "en cours", "...", "...")
        self._tree.insert("", tk.END, iid=item_id, values=values)

        # Auto-scroll so the newest row is always visible.
        children = self._tree.get_children()
        if children:
            self._tree.see(children[-1])

    def complete_journal_entry(
        self,
        item_id: str,
        msg_step_ended: str,
        success: bool,
        duration_s: float,
    ) -> None:
        """Update the pending journal row once the step has finished.

        Safe to call from a background thread.

        Args:
            item_id: The iid returned by ``start_journal_entry``.
            msg_step_ended: Result message from the executor (e.g. ``"OK"`` or
                the error description).
            success: True for a successful step; False for an error.
            duration_s: Wall-clock duration of the step in seconds.
        """
        self.after(0, lambda: self._update_journal_row(item_id, msg_step_ended, success, duration_s))

    def _update_journal_row(self, item_id: str, msg_step_ended: str, success: bool, duration_s: float) -> None:
        """Patch the result columns of an existing journal row on the main thread.

        Args:
            item_id: Treeview iid of the row to update.
            msg_step_ended: Executor result message.
            success: True for OK; False for ERREUR.
            duration_s: Step duration in seconds.
        """
        current = self._tree.item(item_id, "values")
        if not current:
            return

        result_label = "OK" if success else "ERREUR"
        # Preserve date (col 0) and step_started (col 1); replace cols 2-4.
        # TODO PCO : ordre des colonnes pas explicite
        updated = (current[0], current[1], f"{duration_s:.3f}", result_label, msg_step_ended)
        self._tree.item(item_id, values=updated)

    # ------------------------------------------------------------------
    # Internal notification helpers
    # ------------------------------------------------------------------

    def _notify_launch(self) -> None:
        """Fire the on_launch callback when the Lancer button is clicked.

        When no URL source has been selected, a confirmation dialog is shown.
        The launch is aborted if the user declines.
        """
        if not self._url_source_type and not self._confirm_launch_without_source():
            return
        if self._on_launch:
            self._on_launch()

    @staticmethod
    def _confirm_launch_without_source() -> bool:
        """Show a confirmation dialog when no URL source is selected.

        Returns:
            True when the user accepts to continue despite the missing source.
        """
        return messagebox.askokcancel(
            "Aucune source d'URLs",
            "Aucune source d'URLs n'est selectionnee.\n\n"
            "Les etapes OPEN_URL en mode '<<URL>>' seront en erreur.\n\n"
            "Souhaitez-vous continuer quand meme ?",
        )

    def _notify_cancel(self) -> None:
        """Fire the on_cancel callback when the Annuler button is clicked."""
        if self._on_cancel:
            self._on_cancel()

    def _notify_pause(self) -> None:
        """Fire the on_pause callback when the Pause button is clicked."""
        if self._on_pause:
            self._on_pause()

    def _notify_resume(self) -> None:
        """Fire the on_resume callback when the Reprendre button is clicked."""
        if self._on_resume:
            self._on_resume()

    def _notify_refresh_providers(self) -> None:
        """Fire the on_refresh_providers callback when Rafraîchir is clicked."""
        if self._on_refresh_providers:
            self._on_refresh_providers()

    def _on_combobox_selected(self, _event: Any) -> None:
        """Resolve the combobox selection to an id_file and fire the callback.

        Args:
            _event: The Tkinter <<ComboboxSelected>> event (unused).
        """
        display = self._cmb_provider.get()
        id_file = self._provider_id_by_display.get(display)
        if id_file and self._on_provider_selected:
            self._on_provider_selected(id_file)

    def _on_profile_listbox_selected(self, _event: Any) -> None:
        """Resolve the listbox selection to a profile_id and fire the callback.

        Args:
            _event: The Tkinter <<ListboxSelect>> event (unused).
        """
        profile_id = self.get_selected_profile_id()
        if profile_id and self._on_profile_selected_cb:
            self._on_profile_selected_cb(profile_id)

    def _notify_profile_new(self) -> None:
        """Ask the user for a name then fire on_profile_new with it."""
        name = simpledialog.askstring(
            "Nouveau profil",
            "Nom du profil :",
            parent=self,
        )
        if name and self._on_profile_new_cb:
            self._on_profile_new_cb(name.strip())

    def _notify_profile_save(self) -> None:
        """Fire on_profile_save to persist the current form values."""
        if self._on_profile_save_cb:
            self._on_profile_save_cb()

    def _notify_profile_delete(self) -> None:
        """Fire on_profile_delete with the currently selected profile_id."""
        profile_id = self.get_selected_profile_id()
        if profile_id and self._on_profile_delete_cb:
            self._on_profile_delete_cb(profile_id)

    def _on_export_folder_var_changed(self, *_: str) -> None:
        """Fired by the StringVar trace when the export folder Entry content changes.

        Args:
            *_: Tkinter trace arguments (name, index, mode) — unused.
        """
        if self._suppress_form_changed:
            return
        self._export_folder = self._var_export_folder.get()
        self._notify_form_changed()

    def _notify_form_changed(self) -> None:
        """Notify the presenter that the user has modified the launch form."""
        if self._on_form_changed_cb:
            self._on_form_changed_cb()

    @staticmethod
    def _apply_state_recursive(widget: tk.Widget, state: str) -> None:
        """Recursively apply a Tkinter state to a widget and all its children.

        Args:
            widget: Root widget to start from.
            state: "normal" or "disabled".
        """
        with contextlib.suppress(tk.TclError):
            widget.configure(state=state)
        for child in widget.winfo_children():
            ScrapingView._apply_state_recursive(child, state)

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

        def _on_ok() -> None:
            raw = text.get("1.0", tk.END)
            urls = [line.strip() for line in raw.splitlines() if line.strip()]
            self._url_source_type = _URL_SOURCE_MANUAL
            self._url_source_value = urls
            popup.destroy()
            self._notify_form_changed()

        def _on_cancel() -> None:
            # Revert radio button to the previous selection.
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
        """Create the export folder if absent, then reveal it in the file explorer."""
        # Ensure the folder exists before trying to open it.
        path = Path(self._export_folder)
        path.mkdir(parents=True, exist_ok=True)
        open_folder(path)

    # ------------------------------------------------------------------
    # Journal export
    # ------------------------------------------------------------------

    def get_journal_rows(self) -> list[tuple[str, ...]]:
        """Returns the current journal Treeview rows as a list of value tuples.

        Returns:
            Ordered list of row tuples (date, step_started, duration, result, message).
        """
        return [tuple(str(v) for v in self._tree.item(item, "values")) for item in self._tree.get_children()]

    # ------------------------------------------------------------------
    # Message boxes
    # ------------------------------------------------------------------

    @staticmethod
    def show_warning(message: str) -> None:
        """Display a warning message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showwarning("Avertissement", message)
