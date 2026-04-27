"""Tkinter sub-view for the wait_seconds step form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from models.step_catalog import WAIT_UNIT_LABEL_TO_TOKEN
from models.step_scrapping_model import StepValue

class WaitSecondsStepFormView(ttk.Frame):
    """Collects amount and unit for a wait_seconds step."""

    def __init__(self, parent: tk.Widget, initial_value: StepValue = None) -> None:
        super().__init__(parent)
        self._initial_value = initial_value

        self.columnconfigure(1, weight=1)

        amount = ""
        unit_token = "seconds"
        if isinstance(initial_value, dict):
            amount = str(initial_value.get("amount", ""))
            unit_token = str(initial_value.get("unit", "seconds"))
        elif initial_value is not None:
            amount = str(initial_value)

        reverse_unit_map = {value: key for key, value in WAIT_UNIT_LABEL_TO_TOKEN.items()}
        selected_label = reverse_unit_map.get(unit_token, "seconde")

        ttk.Label(self, text="Durée:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self._amount_var = tk.StringVar(value=amount)
        ttk.Entry(self, textvariable=self._amount_var, width=20).grid(row=0, column=1, sticky="w", pady=(0, 8))

        ttk.Label(self, text="Unité:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self._unit_var = tk.StringVar(value=selected_label)
        ttk.Combobox(
            self,
            textvariable=self._unit_var,
            values=list(WAIT_UNIT_LABEL_TO_TOKEN.keys()),
            state="readonly",
            width=18,
        ).grid(row=1, column=1, sticky="w", pady=(0, 8))

    def get_data(self) -> dict[str, Any]:
        return {
            "amount": self._amount_var.get(),
            "unit": self._unit_var.get(),
        }
