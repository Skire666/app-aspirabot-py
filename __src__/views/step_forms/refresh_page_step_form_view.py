"""Tkinter sub-view for the refresh_page step form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shared.step_types import StepValue


class RefreshPageStepFormView(ttk.Frame):
    """Collects refresh options for a refresh_page step."""

    def __init__(self, parent: tk.Widget, initial_value: StepValue = None) -> None:
        super().__init__(parent)
        self._initial_value = initial_value

        clear_cache = False
        if isinstance(initial_value, dict):
            clear_cache = bool(initial_value.get("clear_cache", False))
        elif initial_value is not None:
            clear_cache = bool(initial_value)

        ttk.Label(self, text="Cette étape rafraîchira la page active.").grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 8),
        )

        self._clear_cache_var = tk.BooleanVar(value=clear_cache)
        ttk.Checkbutton(
            self,
            text="Vider le cache avant rafraîchissement",
            variable=self._clear_cache_var,
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

    def get_data(self) -> dict[str, Any]:
        return {"clear_cache": self._clear_cache_var.get()}
