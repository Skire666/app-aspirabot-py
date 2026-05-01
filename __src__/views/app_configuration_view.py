"""Tkinter view for rendering the configuration form."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk
from typing import Any


class AppConfigurationView(ttk.Frame):
    """View component that renders the configuration form.

    Provides inputs for configuration settings and buttons
    for saving or resetting the values. Strictly follows MVP pattern.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the AppConfigurationView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_save: Callable[[], None] | None = None
        self._on_reset: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_change: Callable[[], None] | None = None

        self._log_level_var = tk.StringVar()
        self._folder_logs_var = tk.StringVar()
        self._folder_providers_var = tk.StringVar()
        self._folder_scrapping_var = tk.StringVar()
        self._gui_booting_size_var = tk.StringVar()
        self._gui_booting_fullscreen_var = tk.BooleanVar()

        self._log_level_combo: ttk.Combobox | None = None
        self._btn_cancel: ttk.Button | None = None
        self._lbl_last_write: ttk.Label | None = None

        self._bind_change_events()
        self._create_widgets()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = self._create_form_section(container)
        form_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        footer_frame = self._create_footer_section(container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def _create_form_section(self, parent: tk.Widget) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="Configuration")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)

        self._add_enum_row(frame, 0, "Niveau log", self._log_level_var)
        self._add_path_row(frame, 1, "Dossier logs", self._folder_logs_var)
        self._add_path_row(frame, 2, "Dossier providers", self._folder_providers_var)
        self._add_path_row(frame, 3, "Dossier scrapping", self._folder_scrapping_var)
        self._add_text_row(frame, 4, "Taille GUI (WxH)", self._gui_booting_size_var)
        self._add_bool_row(frame, 5, "GUI plein ecran", self._gui_booting_fullscreen_var)

        return frame

    def _create_footer_section(self, parent: tk.Widget) -> ttk.Frame:
        frame = ttk.Frame(parent)

        ttk.Button(frame, text="Reset", command=self._notify_reset).pack(side=tk.LEFT, padx=5)
        self._btn_cancel = ttk.Button(
            frame,
            text="Annuler",
            command=self._notify_cancel,
            state=tk.DISABLED,
        )
        self._btn_cancel.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Sauvegarder", command=self._notify_save).pack(side=tk.LEFT, padx=5)

        self._lbl_last_write = ttk.Label(frame, text="Derniere ecriture: --")
        self._lbl_last_write.pack(side=tk.RIGHT, padx=5)

        return frame

    def _add_enum_row(self, frame: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        combo = ttk.Combobox(frame, textvariable=var, state="readonly")
        combo.grid(row=row, column=1, columnspan=2, sticky="ew", padx=6, pady=4)
        self._log_level_combo = combo

    def _add_text_row(self, frame: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=var).grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=6,
            pady=4,
        )

    def _add_path_row(self, frame: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(frame, text="Parcourir", command=lambda: self._browse_directory(var)).grid(
            row=row,
            column=2,
            sticky="e",
            padx=6,
            pady=4,
        )

    def _add_bool_row(self, frame: ttk.Frame, row: int, label: str, var: tk.BooleanVar) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(frame, variable=var).grid(row=row, column=1, sticky="w", padx=6, pady=4)

    def _browse_directory(self, target_var: tk.StringVar) -> None:
        current = target_var.get().strip()
        if current:
            directory = filedialog.askdirectory(initialdir=current)
        else:
            directory = filedialog.askdirectory()
        if directory:
            target_var.set(directory)

    def _bind_change_events(self) -> None:
        for var in (
            self._log_level_var,
            self._folder_logs_var,
            self._folder_providers_var,
            self._folder_scrapping_var,
            self._gui_booting_size_var,
            self._gui_booting_fullscreen_var,
        ):
            var.trace_add("write", self._notify_change)

    def set_callbacks(
        self,
        on_save: Callable[[], None],
        on_reset: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Sets callbacks for save and reset actions.

        Args:
            on_save: Callback fired when the user clicks save.
            on_reset: Callback fired when the user clicks reset.
            on_cancel: Callback fired when the user clicks cancel.
        """
        self._on_save = on_save
        self._on_reset = on_reset
        self._on_cancel = on_cancel

    def set_on_change_callback(self, callback: Callable[[], None]) -> None:
        """Sets a callback fired when any form field changes.

        Args:
            callback: Callback invoked on user edits.
        """
        self._on_change = callback

    def set_cancel_enabled(self, is_enabled: bool) -> None:
        """Enables or disables the cancel button.

        Args:
            is_enabled: True to enable, False to disable.
        """
        if self._btn_cancel is None:
            return
        state = tk.NORMAL if is_enabled else tk.DISABLED
        self._btn_cancel.config(state=state)

    def set_log_level_options(self, options: list[str]) -> None:
        """Sets the available options for the log level combobox.

        Args:
            options: Allowed log level values.
        """
        if self._log_level_combo is None:
            return
        self._log_level_combo.configure(values=options)
        if options and self._log_level_var.get() not in options:
            self._log_level_var.set(options[0])

    def load_data(self, data: dict[str, Any]) -> None:
        """Loads configuration values into the form widgets.

        Args:
            data: Mapping of configuration keys to values.
        """
        self._log_level_var.set(self._safe_text(data.get("log_level_enum")))
        self._folder_logs_var.set(self._safe_text(data.get("folder_logs")))
        self._folder_providers_var.set(self._safe_text(data.get("folder_providers")))
        self._folder_scrapping_var.set(self._safe_text(data.get("folder_scrapping")))
        self._gui_booting_size_var.set(self._safe_text(data.get("gui_booting_size")))
        self._gui_booting_fullscreen_var.set(bool(data.get("gui_booting_fullscreen", False)))

    def get_data(self) -> dict[str, Any]:
        """Returns the current form values.

        Returns:
            Dictionary containing current widget values.
        """
        return {
            "log_level_enum": self._log_level_var.get(),
            "folder_logs": self._folder_logs_var.get(),
            "folder_providers": self._folder_providers_var.get(),
            "folder_scrapping": self._folder_scrapping_var.get(),
            "gui_booting_size": self._gui_booting_size_var.get(),
            "gui_booting_fullscreen": self._gui_booting_fullscreen_var.get(),
        }

    def set_last_write_time(self, display_value: str) -> None:
        """Updates the last write time label.

        Args:
            display_value: Human-readable last write time string.
        """
        if self._lbl_last_write is None:
            return
        self._lbl_last_write.config(text=f"Derniere ecriture: {display_value}")

    def ask_reset_confirmation(self) -> bool:
        """Asks the user to confirm a reset action.

        Returns:
            True if the user confirms the reset.
        """
        return messagebox.askyesno("Confirmation", "Reinitialiser la configuration ?")

    def show_error(self, message: str) -> None:
        """Displays an error dialog.

        Args:
            message: Error message to display.
        """
        messagebox.showerror("Erreur", message)

    def _notify_save(self) -> None:
        if self._on_save:
            self._on_save()

    def _notify_reset(self) -> None:
        if self._on_reset:
            self._on_reset()

    def _notify_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()

    def _notify_change(self, *_: str) -> None:
        if self._on_change:
            self._on_change()

    @staticmethod
    def _safe_text(value: Any) -> str:
        return "" if value is None else str(value)
