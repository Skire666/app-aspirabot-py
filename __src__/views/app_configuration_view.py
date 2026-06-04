"""Tkinter view for rendering the configuration form."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from view_models.app_configuration_view_model import AppConfigurationViewModel
from views.components.canvas_checkbox import CanvasCheckbox


class AppConfigurationView(ttk.Frame):
    """View component that renders the configuration form.

    All form field Vars live on the ViewModel; this View only builds widgets,
    binds them to those Vars, and dispatches user actions to VM action methods.
    """

    def __init__(self, parent: tk.Widget, vm: AppConfigurationViewModel) -> None:
        """Initializes the AppConfigurationView component bound to *vm*.

        Args:
            parent: The parent Tkinter widget.
            vm: The AppConfigurationViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm
        self._view_traces: list[tuple[tk.Variable, str]] = []

        self._log_level_combo: ttk.Combobox | None = None
        self._browser_engine_combo: ttk.Combobox | None = None
        self._btn_cancel: ttk.Button | None = None
        self._btn_save: ttk.Button | None = None

        self._create_widgets()
        self._bind_vm_vars()
        # Register View as dialog providers.
        vm.bind_ask_reset(self._ask_reset_confirmation)
        vm.bind_show_error(self._show_error)

    def _create_widgets(self) -> None:
        """Build form and footer sections."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = self._create_form_section(container)
        form_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        footer_frame = self._create_footer_section(container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def _create_form_section(self, parent: tk.Widget) -> ttk.LabelFrame:
        """Build the form rows inside a labeled frame."""
        frame = ttk.LabelFrame(parent, text="Configuration")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)

        self._add_enum_row_log(frame, 0, "Niveau log", self._vm.log_level_var)
        self._add_path_row(frame, 1, "Dossier logs", self._vm.folder_logs_var)
        self._add_path_row(frame, 2, "Dossier scénarios", self._vm.folder_scenarios_var)
        self._add_path_row(frame, 3, "Dossier scraping", self._vm.folder_scraping_var)
        self._add_text_row(frame, 4, "Taille fenêtre libre (WxH)", self._vm.gui_booting_size_var)
        self._add_bool_row(frame, 5, "Démarrer en plein écran", self._vm.gui_booting_fullscreen_var)
        self._add_enum_row_browser_engine(frame, 6, "Moteur de navigation", self._vm.browser_engine_var)

        return frame

    def _create_footer_section(self, parent: tk.Widget) -> ttk.Frame:
        """Build the footer with action buttons and last-write label."""
        frame = ttk.Frame(parent)

        ttk.Button(frame, text="Réinitialiser", command=lambda: self._vm.reset()).pack(side=tk.LEFT, padx=(0, 5))
        self._btn_cancel = ttk.Button(frame, text="Annuler", command=lambda: self._vm.cancel(), state=tk.DISABLED)
        self._btn_cancel.pack(side=tk.LEFT, padx=5)
        self._btn_save = ttk.Button(
            frame, text="Sauvegarder les modifications", command=lambda: self._vm.save(), state=tk.DISABLED
        )
        self._btn_save.pack(side=tk.LEFT, padx=5)

        self._lbl_last_write = ttk.Label(frame, textvariable=self._vm.last_write_time_var)
        self._lbl_last_write.pack(side=tk.RIGHT, padx=5)

        return frame

    def _add_enum_row_log(self, frame: ttk.Frame | ttk.LabelFrame, row: int, label: str, var: tk.StringVar) -> None:
        """Add a log-level combobox row."""
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        combo = ttk.Combobox(frame, textvariable=var, state="readonly")
        combo.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self._log_level_combo = combo

    def _add_enum_row_browser_engine(
        self, frame: ttk.Frame | ttk.LabelFrame, row: int, label: str, var: tk.StringVar
    ) -> None:
        """Add a browser-engine combobox row."""
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        combo = ttk.Combobox(frame, textvariable=var, state="readonly")
        combo.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self._browser_engine_combo = combo

    @staticmethod
    def _add_text_row(frame: ttk.Frame | ttk.LabelFrame, row: int, label: str, var: tk.StringVar) -> None:
        """Add a plain text entry row."""
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

    def _add_path_row(self, frame: ttk.Frame | ttk.LabelFrame, row: int, label: str, var: tk.StringVar) -> None:
        """Add a path entry row with a Browse button."""
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Parcourir", command=lambda: self._browse_directory(var)).grid(
            row=row, column=2, sticky="e", padx=5, pady=5
        )

    @staticmethod
    def _add_bool_row(frame: ttk.Frame | ttk.LabelFrame, row: int, label: str, var: tk.BooleanVar) -> None:
        """Add a boolean checkbox row."""
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        CanvasCheckbox(frame, variable=var).grid(row=row, column=1, sticky="w", padx=5, pady=5)

    @staticmethod
    def _browse_directory(target_var: tk.StringVar) -> None:
        """Open a directory chooser and update *target_var*.

        Args:
            target_var: The ViewModel StringVar to update with the chosen path.
        """
        current = target_var.get().strip()
        directory = filedialog.askdirectory(initialdir=current) if current else filedialog.askdirectory()
        if directory:
            target_var.set(directory)

    # ------------------------------------------------------------------
    # ViewModel bindings
    # ------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace listeners on ViewModel Vars; ids stored for teardown."""
        # Form changes dispatch to VM (one lambda per var to capture each binding correctly).
        for var in (
            self._vm.log_level_var,
            self._vm.folder_logs_var,
            self._vm.folder_scenarios_var,
            self._vm.folder_scraping_var,
            self._vm.gui_booting_size_var,
            self._vm.gui_booting_fullscreen_var,
            self._vm.browser_engine_var,
        ):
            self._view_traces.append((var, var.trace_add("write", lambda *_: self._vm.form_changed())))

        # Button enable states and combo option lists.
        for var, cb in [
            (self._vm.is_cancel_enabled_var, self._sync_cancel_btn),
            (self._vm.log_level_options_version_var, self._sync_log_level_options),
            (self._vm.browser_engine_options_version_var, self._sync_browser_engine_options),
        ]:
            self._view_traces.append((var, var.trace_add("write", cb)))

    def teardown(self) -> None:
        """Detach all view-owned VM traces and dispose the ViewModel."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()
        self._vm.dispose()

    def _sync_cancel_btn(self, *_: object) -> None:
        """Mirror is_cancel_enabled_var onto the Cancel and Save buttons."""
        enabled = self._vm.is_cancel_enabled_var.get()
        state = tk.NORMAL if enabled else tk.DISABLED
        if self._btn_cancel is not None:
            self._btn_cancel.config(state=state)
        if self._btn_save is not None:
            self._btn_save.config(state=state)

    def _sync_log_level_options(self, *_: object) -> None:
        """Update the log-level combobox values from the ViewModel."""
        if self._log_level_combo is None:
            return
        options = self._vm.get_log_level_options()
        self._log_level_combo.configure(values=options)
        if options and self._vm.log_level_var.get() not in options:
            self._vm.log_level_var.set(options[0])

    def _sync_browser_engine_options(self, *_: object) -> None:
        """Update the browser-engine combobox values from the ViewModel."""
        if self._browser_engine_combo is None:
            return
        options = self._vm.get_browser_engine_options()
        self._browser_engine_combo.configure(values=options)
        if options and self._vm.browser_engine_var.get() not in options:
            self._vm.browser_engine_var.set(options[0])

    # ------------------------------------------------------------------
    # Dialog providers — registered on ViewModel
    # ------------------------------------------------------------------

    @staticmethod
    def _ask_reset_confirmation() -> bool:
        """Show a reset-confirmation dialog synchronously.

        Returns:
            True when the user confirms the reset.
        """
        return messagebox.askyesno("Confirmation", "Réinitialiser la configuration ?")

    @staticmethod
    def _show_error(message: str) -> None:
        """Display a modal error dialog.

        Args:
            message: Error message to display.
        """
        messagebox.showerror("Erreur", message)


# EOF
