"""Standalone demo for the EditableTable component.

Run with:
    python __tools__/excel.py
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "__src__"))

from views.components.excel_grid.excel_grid import (  # type: ignore[import]
    ActionColumnDef,
    EditableTable,
    TableConfig,
    TextColumnDef,
)


def _browse_folder(_row_idx: int, row_data: dict[str, str]) -> str | None:
    """Open a folder-picker dialog and return the chosen path, or None to cancel."""
    path = filedialog.askdirectory(title="Sélectionner un dossier", initialdir=row_data.get("folder") or "/")
    return path or None


def _build_config() -> TableConfig:
    return TableConfig(
        columns=[
            TextColumnDef(key="name", header="Nom", default="Nouveau", width=180),
            TextColumnDef(key="age", header="Âge", default="0", width=80),
            TextColumnDef(key="folder", header="Dossier", default="", width=260),
            ActionColumnDef(
                key="browse", header="", label="📂 Parcourir", target_key="folder", handler=_browse_folder, width=120
            ),
        ],
        initial_data=[
            {"name": "Alice", "age": "30", "folder": "/home/alice"},
            {"name": "Bob", "age": "25", "folder": ""},
            {"name": "Charlie", "age": "35", "folder": "/tmp"},
        ],
        confirm_delete=True,
        confirm_clear=True,
        on_change=_on_data_changed,
        default_sort_key="name",
        default_sort_ascending=True,
    )


def _on_data_changed(data: list[dict[str, str]]) -> None:
    print(f"[on_change] {len(data)} ligne(s) :")
    for i, row in enumerate(data):
        print(f"  [{i}] {row}")


def main() -> None:
    """Launch the demo window."""
    root = tk.Tk()
    root.title("EditableTable — démo")
    root.geometry("900x480")

    config = _build_config()
    table = EditableTable(root, config)
    table.pack(fill="both", expand=True, padx=8, pady=8)

    # Bottom status bar showing live row count.
    status_var = tk.StringVar(value=f"{len(config.initial_data)} ligne(s)")
    tk.Label(root, textvariable=status_var, anchor="w").pack(side="bottom", fill="x", padx=8, pady=(0, 4))

    def _refresh_status(data: list[dict[str, str]]) -> None:
        status_var.set(f"{len(data)} ligne(s)")
        _on_data_changed(data)

    # Override on_change to also update the status bar.
    table.config.on_change = _refresh_status

    root.mainloop()


if __name__ == "__main__":
    main()
