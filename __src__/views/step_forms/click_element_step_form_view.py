"""Tkinter sub-view for the click_element step form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shared.step_types import StepValue


class ClickElementStepFormView(ttk.Frame):
    """Collects click selector and mode flags."""

    def __init__(self, parent: tk.Widget, initial_value: StepValue = None) -> None:
        super().__init__(parent)
        self._initial_value = initial_value

        self.columnconfigure(1, weight=1)

        selector = ""
        normal = True
        forced = False
        js_direct = False
        verify_present = False

        if isinstance(initial_value, dict):
            selector = str(initial_value.get("selector", ""))
            normal = bool(initial_value.get("normal", True))
            forced = bool(initial_value.get("forced", False))
            js_direct = bool(initial_value.get("js_direct", False))
            verify_present = bool(initial_value.get("verify_present", False))
        elif initial_value is not None:
            selector = str(initial_value)

        ttk.Label(self, text="Sélecteur CSS:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        self._selector_var = tk.StringVar(value=selector)
        selector_entry = ttk.Entry(self, textvariable=self._selector_var, width=50)
        selector_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        selector_entry.focus_set()

        self._normal_var = tk.BooleanVar(value=normal)
        self._forced_var = tk.BooleanVar(value=forced)
        self._js_direct_var = tk.BooleanVar(value=js_direct)
        self._verify_present_var = tk.BooleanVar(value=verify_present)

        ttk.Checkbutton(self, text="Normal", variable=self._normal_var).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Checkbutton(self, text="Forced", variable=self._forced_var).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Checkbutton(self, text="JS Direct", variable=self._js_direct_var).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Checkbutton(self, text="Vérifier présent du bouton", variable=self._verify_present_var).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )

    def get_data(self) -> dict[str, Any]:
        return {
            "selector": self._selector_var.get(),
            "normal": self._normal_var.get(),
            "forced": self._forced_var.get(),
            "js_direct": self._js_direct_var.get(),
            "verify_present": self._verify_present_var.get(),
        }
