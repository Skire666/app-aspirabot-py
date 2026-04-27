"""Tkinter sub-view for the check_if_image_here step form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shared.step_types import StepValue


class CheckIfImageHereStepFormView(ttk.Frame):
    """Collects coordinate bounds for image-area checks."""

    def __init__(self, parent: tk.Widget, initial_value: StepValue = None) -> None:
        super().__init__(parent)
        self._initial_value = initial_value

        self.columnconfigure(1, weight=1)

        w1 = "0"
        w2 = "0"
        h1 = "0"
        h2 = "0"

        if isinstance(initial_value, dict):
            w1 = str(initial_value.get("w1", 0))
            w2 = str(initial_value.get("w2", 0))
            h1 = str(initial_value.get("h1", 0))
            h2 = str(initial_value.get("h2", 0))

        self._w1_var = tk.StringVar(value=w1)
        self._w2_var = tk.StringVar(value=w2)
        self._h1_var = tk.StringVar(value=h1)
        self._h2_var = tk.StringVar(value=h2)

        ttk.Label(self, text="W1:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(self, text="W2:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(self, text="H1:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Label(self, text="H2:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        ttk.Entry(self, textvariable=self._w1_var, width=16).grid(row=0, column=1, sticky="w", pady=(0, 8))
        ttk.Entry(self, textvariable=self._w2_var, width=16).grid(row=1, column=1, sticky="w", pady=(0, 8))
        ttk.Entry(self, textvariable=self._h1_var, width=16).grid(row=2, column=1, sticky="w", pady=(0, 8))
        ttk.Entry(self, textvariable=self._h2_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))

        ttk.Label(self, text="Condition: W1 < X < W2 et H1 < Y < H2").grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )

    def get_data(self) -> dict[str, Any]:
        return {
            "w1": self._w1_var.get(),
            "w2": self._w2_var.get(),
            "h1": self._h1_var.get(),
            "h2": self._h2_var.get(),
        }
