"""Toplevel popup for interactively testing the URL-transformer rule.

Passive test window: reads the current regexp / prefix / trailing-slash Vars
from ``ExecutorViewModel`` at click-time and runs them through the pure
``transformer_url`` utility. No Presenter involvement — this is a stateless
preview tool, not a persisted action.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk

from shared.exception_util import AspirabotBaseError
from shared.url_util import transformer_url
from view_models.executor_view_model import ExecutorViewModel

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlTransformerTestView(tk.Toplevel):
    """Popup letting the user paste URLs and preview the transformer_url output."""

    def __init__(self, parent: tk.Widget, vm: ExecutorViewModel) -> None:
        """Build the popup and wire the Convertir/Fermer buttons.

        Args:
            parent: Parent Tkinter container (the executor view).
            vm: The ExecutorViewModel providing the current transformer settings.
        """
        super().__init__(parent)
        self._vm = vm
        self.title("Tester la transformation d'URLs")
        self.geometry("760x480")
        self.resizable(True, True)
        self._create_widgets()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build the two side-by-side text panes and the action buttons row."""
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._txt_input = self._create_text_pane(self, column=0, title="URLs à transformer (une par ligne) :")  # pyright: ignore[reportArgumentType]
        self._txt_output = self._create_text_pane(self, column=1, title="Résultat :", readonly=True)  # pyright: ignore[reportArgumentType]

        btn_row = ttk.Frame(self)
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(btn_row, text="Fermer", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(btn_row, text="Convertir", command=self._on_convert_clicked).pack(side=tk.RIGHT, padx=(0, 6))

    @staticmethod
    def _create_text_pane(parent: tk.Widget, column: int, title: str, readonly: bool = False) -> tk.Text:
        """Build one labeled, scrollable Text pane.

        Args:
            parent: The Toplevel to grid into.
            column: Grid column index (0 = left, 1 = right).
            title: Label text shown above the pane.
            readonly: When True, the Text widget starts DISABLED.

        Returns:
            The created ``tk.Text`` widget.
        """
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew", padx=8, pady=8)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text=title).grid(row=0, column=0, sticky="w")

        container = ttk.Frame(frame)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL)
        txt = tk.Text(container, wrap=tk.NONE, yscrollcommand=vsb.set, state=tk.DISABLED if readonly else tk.NORMAL)
        vsb.configure(command=txt.yview)  # type: ignore[reportUnknownMemberType]
        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        return txt

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_convert_clicked(self) -> None:
        """Read input URLs, apply the current transformer settings, and display the result."""
        raw = self._txt_input.get("1.0", tk.END)
        urls = [line for line in raw.splitlines() if line.strip()]
        pattern = self._vm.transformer_url_regexp_var.get()
        base = self._vm.transformer_url_base_var.get()
        trailing_slash = self._vm.transformer_url_trailing_slash_var.get()
        try:
            results = [transformer_url(url, pattern, base, trailing_slash) for url in urls]
        except AspirabotBaseError as e:
            messagebox.showerror("Transformation impossible", str(e), parent=self)
            return
        self._write_output("\n".join(results))

    def _write_output(self, text: str) -> None:
        """Replace the content of the read-only output pane.

        Args:
            text: New text content to display.
        """
        self._txt_output.configure(state=tk.NORMAL)
        self._txt_output.delete("1.0", tk.END)
        self._txt_output.insert("1.0", text)
        self._txt_output.configure(state=tk.DISABLED)


# EOF
