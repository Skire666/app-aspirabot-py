"""Tkinter sub-view for the download_image step form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from models.step_scrapping_model import StepValue


class DownloadImageStepFormView(ttk.Frame):
    """Collects image download options without performing validation."""

    def __init__(self, parent: tk.Widget, initial_value: StepValue = None) -> None:
        super().__init__(parent)
        self._initial_value = initial_value

        self.columnconfigure(1, weight=1)

        mode = "largest"
        min_width = "0"
        min_height = "0"
        max_width = "0"
        max_height = "0"

        if isinstance(initial_value, dict):
            mode = str(initial_value.get("mode", "largest"))
            min_width = str(initial_value.get("min_width", 0))
            min_height = str(initial_value.get("min_height", 0))
            max_width = str(initial_value.get("max_width", 0))
            max_height = str(initial_value.get("max_height", 0))

        self._mode_var = tk.StringVar(value=mode if mode in {"largest", "first", "all"} else "largest")
        self._min_width_var = tk.StringVar(value=min_width)
        self._min_height_var = tk.StringVar(value=min_height)
        self._max_width_var = tk.StringVar(value=max_width)
        self._max_height_var = tk.StringVar(value=max_height)

        ttk.Label(self, text="Mode de téléchargement:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        ttk.Radiobutton(self, text="La plus grande image", variable=self._mode_var, value="largest").grid(
            row=0,
            column=1,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Radiobutton(self, text="La première image", variable=self._mode_var, value="first").grid(
            row=1,
            column=1,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Radiobutton(self, text="Toutes les images", variable=self._mode_var, value="all").grid(
            row=2,
            column=1,
            sticky="w",
            pady=(0, 8),
        )

        ttk.Label(self, text="Largeur min (W):").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(self, textvariable=self._min_width_var, width=16).grid(row=3, column=1, sticky="w", pady=(0, 8))
        ttk.Label(self, text="Hauteur min (H):").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(self, textvariable=self._min_height_var, width=16).grid(row=4, column=1, sticky="w", pady=(0, 8))
        ttk.Label(self, text="Largeur max (W):").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(self, textvariable=self._max_width_var, width=16).grid(row=5, column=1, sticky="w", pady=(0, 8))
        ttk.Label(self, text="Hauteur max (H):").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(self, textvariable=self._max_height_var, width=16).grid(row=6, column=1, sticky="w", pady=(0, 8))

    def get_data(self) -> dict[str, Any]:
        return {
            "mode": self._mode_var.get(),
            "min_width": self._min_width_var.get(),
            "min_height": self._min_height_var.get(),
            "max_width": self._max_width_var.get(),
            "max_height": self._max_height_var.get(),
        }
