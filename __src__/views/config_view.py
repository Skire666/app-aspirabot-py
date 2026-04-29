"""Tkinter view for rendering the configuration form."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional


class ConfigView(ttk.Frame):
    """View component that renders the configuration form.

    Provides inputs for configuration settings and buttons
    for saving or resetting the values. Strictly follows MVP pattern.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ConfigView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_save_clicked: Optional[Callable[[Dict[str, str]], None]] = None
        self._on_reset_clicked: Optional[Callable[[], None]] = None

        self._entries: Dict[str, ttk.Entry] = {}

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs UI elements for the configuration form."""
        form_frame = ttk.LabelFrame(self, text="Configuration Settings", padding=(10, 10))
        form_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        fields = [
            "log_level",
            "folder_logs",
            "folder_brokens",
            "folder_output",
            "folder_providers",
            "folder_tmp_chromium",
        ]
        for idx, field in enumerate(fields):
            ttk.Label(form_frame, text=field.replace("_", " ").title() + ":").grid(
                row=idx, column=0, padx=5, pady=5, sticky=tk.W
            )
            entry = ttk.Entry(form_frame, width=50)
            entry.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.EW)
            self._entries[field] = entry

        form_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Save", command=self._notify_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self._notify_reset).pack(side=tk.LEFT, padx=5)

    def set_save_callback(self, callback: Callable[[Dict[str, str]], None]) -> None:
        """Sets the callback to invoke on Save button click.

        Args:
            callback: The function to call with the new configuration data.
        """
        self._on_save_clicked = callback

    def set_reset_callback(self, callback: Callable[[], None]) -> None:
        """Sets the callback to invoke on Reset button click.

        Args:
            callback: The function to call when resetting the form.
        """
        self._on_reset_clicked = callback

    def display_config(self, config_data: Dict[str, str]) -> None:
        """Updates the input fields with the provided configuration data.

        Args:
            config_data: A dictionary containing the configuration fields and their values.
        """
        for field, value in config_data.items():
            if field in self._entries:
                self._entries[field].delete(0, tk.END)
                self._entries[field].insert(0, str(value))

    def _notify_save(self) -> None:
        """Triggers the save callback with the current input values."""
        if self._on_save_clicked:
            data = {field: entry.get() for field, entry in self._entries.items()}
            self._on_save_clicked(data)

    def _notify_reset(self) -> None:
        """Triggers the reset callback."""
        if self._on_reset_clicked:
            self._on_reset_clicked()
