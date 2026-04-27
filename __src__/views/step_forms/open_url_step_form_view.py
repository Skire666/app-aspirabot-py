"""Tkinter sub-view for the open_url step form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shared.step_types import StepValue


class OpenUrlStepFormView(ttk.Frame):
    """Collects a URL string for the open_url step."""

    def __init__(self, parent: tk.Widget, initial_value: StepValue = None) -> None:
        super().__init__(parent)
        self._initial_value = initial_value

        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="URL:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        initial_url = ""
        if isinstance(initial_value, dict):
            initial_url = str(initial_value.get("url", ""))
        elif initial_value is not None:
            initial_url = str(initial_value)

        self._url_var = tk.StringVar(value=initial_url)
        self._url_entry = ttk.Entry(self, textvariable=self._url_var, width=50)
        self._url_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self._url_entry.focus_set()

    def get_data(self) -> dict[str, Any]:
        return {"url": self._url_var.get()}
