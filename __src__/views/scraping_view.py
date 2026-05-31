"""Tkinter view for the live scraping panel.

Displays launch context, real-time statistics, control buttons, and a
scrollable journal. All state is driven by ScrapingViewModel Vars.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk

from shared.constants import C_COLOR_ORANGE_BLINKING
from view_models.scraping_view_model import ScrapingViewModel
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_BLINK_INTERVAL_MS = 500

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingView(ttk.Frame):
    """Live scraping panel: context info, stats, piloting buttons, and journal.

    Sections:
        1. Launch context (scenario name, profile, export folder).
        2. Real-time scraping statistics (polled every 500 ms by the Presenter).
        3. Piloting buttons (launch, cancel, pause, resume).
        4. Journal (read-only text log + export info).

    All display state is driven by ViewModel Vars via ``trace_add``.  User
    actions call ViewModel action methods.  The View registers itself as the
    error-dialog provider on the ViewModel.
    """

    def __init__(self, parent: tk.Widget, vm: ScrapingViewModel) -> None:
        """Build the widget structure and bind to the ViewModel.

        Args:
            parent: Parent Tkinter container.
            vm: The ScrapingViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm

        # Blink state for the Reprendre button.
        self._blink_active: bool = False
        self._blink_phase: bool = False

        self._create_widgets()
        self._bind_vm_vars()
        # Register View as error-dialog provider.
        vm.bind_show_error(self._show_error)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build all four sections."""
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self._create_info_section(outer)
        self._create_stats_section(outer)
        self._create_piloting_section(outer)
        self._create_journal_section(outer)

    def _create_info_section(self, parent: tk.Widget) -> None:
        """Section 1 — launch context (scenario, profile, folder)."""
        frame = HorizontalLineFrame(parent, text="Informations sur le lancement")
        frame.pack(fill=tk.X)
        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(grid, text="Scénario :").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        ttk.Label(grid, textvariable=self._vm.scenario_name_var).grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(grid, text="Profil :").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        ttk.Label(grid, textvariable=self._vm.profile_name_var).grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(grid, text="Dossier d'export :").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        ttk.Label(grid, textvariable=self._vm.folder_var).grid(row=2, column=1, sticky=tk.W, pady=(0, 5))

        FolderLinkWidget(
            grid, title="Dossier", path="Cliquer pour ouvrir", callback=lambda: self._vm.open_folder()
        ).grid(row=2, column=2, padx=(10, 0), pady=(0, 5))

    def _create_stats_section(self, parent: tk.Widget) -> None:
        """Section 2 — real-time scraping statistics, bound to ViewModel Vars."""
        frame = HorizontalLineFrame(parent, text="Informations sur le scraping")
        frame.pack(fill=tk.X)
        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X, padx=5, pady=(0, 5))

        rows = [
            ("Processus :", self._vm.process_status_var),
            ("Dernière URL ouverte :", self._vm.stat_last_url_opended_var),
            ("Onglets / URL Page[0] :", self._vm.stat_browser_tabs_var),
            ("Statistiques globales :", self._vm.stat_global_var),
            ("Statistiques OpenURL :", self._vm.stat_open_url_var),
            ("Statistiques ClickOn :", self._vm.stat_click_var),
            ("Démarrage :", self._vm.stat_started_var),
            ("Étape en cours :", self._vm.stat_step_var),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(grid, text=label).grid(row=i, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
            ttk.Label(grid, textvariable=var).grid(row=i, column=1, sticky=tk.W, pady=(0, 5))

    def _create_piloting_section(self, parent: tk.Widget) -> None:
        """Section 3 — launch / cancel / pause / resume control buttons."""
        frame = HorizontalLineFrame(parent, text="Pilotage")
        frame.pack(fill=tk.X)
        row = ttk.Frame(frame)
        row.pack(padx=5, pady=(0, 5), anchor=tk.W)

        self._btn_launch = ttk.Button(
            row, text="Lancer le scraping", command=lambda: self._vm.launch(), state=tk.DISABLED
        )
        self._btn_launch.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_cancel = ttk.Button(row, text="Annuler (kill)", command=lambda: self._vm.cancel(), state=tk.DISABLED)
        self._btn_cancel.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_pause = ttk.Button(row, text="Mettre en pause", command=lambda: self._vm.pause(), state=tk.DISABLED)
        self._btn_pause.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_resume = tk.Button(row, text="Reprendre", command=lambda: self._vm.resume(), state=tk.DISABLED)
        self._btn_resume_default_bg: str = self._btn_resume.cget("background")
        self._btn_resume.pack(side=tk.LEFT)

    def _create_journal_section(self, parent: tk.Widget) -> None:
        """Section 4 — scrollable read-only journal."""
        frame = HorizontalLineFrame(parent, text="Journal")
        frame.pack(fill=tk.BOTH, expand=True)

        txt_frame = ttk.Frame(frame)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self._txt_journal = tk.Text(txt_frame, state=tk.DISABLED, wrap=tk.NONE, height=12)
        sb_y = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=self._txt_journal.yview)
        sb_x = ttk.Scrollbar(txt_frame, orient=tk.HORIZONTAL, command=self._txt_journal.xview)
        self._txt_journal.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self._txt_journal.pack(fill=tk.BOTH, expand=True)

        self._lbl_journal_path = ttk.Label(frame, textvariable=self._vm.journal_path_var)
        self._lbl_journal_path.pack(padx=5, pady=(0, 5), anchor=tk.W)

    # ------------------------------------------------------------------
    # ViewModel bindings
    # ------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace_add listeners on all relevant ViewModel Vars."""
        # Piloting button states.
        self._vm.is_launch_btn_enabled_var.trace_add("write", self._sync_launch_btn)
        self._vm.is_cancel_btn_enabled_var.trace_add("write", self._sync_cancel_btn)
        self._vm.is_pause_enabled_var.trace_add("write", self._sync_pause_btn)
        self._vm.is_resume_active_var.trace_add("write", self._sync_resume_active)

        # Journal.
        self._vm.journal_version_var.trace_add("write", self._sync_journal_append)
        self._vm.journal_clear_var.trace_add("write", self._sync_journal_clear)

    # ------------------------------------------------------------------
    # Sync methods (called by trace_add)
    # ------------------------------------------------------------------

    def _sync_launch_btn(self, *_: object) -> None:
        """Mirror is_launch_btn_enabled_var onto the launch button."""
        state = tk.NORMAL if self._vm.is_launch_btn_enabled_var.get() else tk.DISABLED
        self._btn_launch.configure(state=state)

    def _sync_cancel_btn(self, *_: object) -> None:
        """Mirror is_cancel_btn_enabled_var onto the cancel button."""
        state = tk.NORMAL if self._vm.is_cancel_btn_enabled_var.get() else tk.DISABLED
        self._btn_cancel.configure(state=state)

    def _sync_pause_btn(self, *_: object) -> None:
        """Mirror is_pause_enabled_var onto the pause button."""
        state = tk.NORMAL if self._vm.is_pause_enabled_var.get() else tk.DISABLED
        self._btn_pause.configure(state=state)

    def _sync_resume_active(self, *_: object) -> None:
        """Enable the Reprendre button and start/stop its orange blink."""
        active = self._vm.is_resume_active_var.get()
        self._btn_resume.configure(state=tk.NORMAL if active else tk.DISABLED)
        if active and not self._blink_active:
            self._blink_active = True
            self._blink_resume()
        elif not active:
            self._blink_active = False
            self._btn_resume.configure(bg=self._btn_resume_default_bg)

    def _blink_resume(self) -> None:
        """Toggle the resume button colour every 500 ms while active."""
        if not self._blink_active:
            return
        self._blink_phase = not self._blink_phase
        bg = C_COLOR_ORANGE_BLINKING if self._blink_phase else self._btn_resume_default_bg
        self._btn_resume.configure(bg=bg)
        self.after(_BLINK_INTERVAL_MS, self._blink_resume)

    def _sync_journal_append(self, *_: object) -> None:
        """Append the latest line from journal_append_var to the Text widget."""
        line = self._vm.journal_append_var.get()
        if line:
            self._txt_journal.configure(state=tk.NORMAL)
            self._txt_journal.insert(tk.END, line + "\n")
            self._txt_journal.see(tk.END)
            self._txt_journal.configure(state=tk.DISABLED)

    def _sync_journal_clear(self, *_: object) -> None:
        """Clear the journal Text widget on every increment of journal_clear_var."""
        self._txt_journal.configure(state=tk.NORMAL)
        self._txt_journal.delete("1.0", tk.END)
        self._txt_journal.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Dialog provider — registered on ViewModel
    # ------------------------------------------------------------------

    def _show_error(self, title: str, message: str) -> None:
        """Display a modal error dialog.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        messagebox.showerror(title, message, parent=self)


# EOF
