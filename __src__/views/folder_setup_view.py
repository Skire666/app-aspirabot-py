"""Modal dialog prompting the user to configure the scenarios folder at first launch."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import filedialog, ttk

from shared.i18n_fra import (
    C_FOLDER_SETUP_BROWSE_BTN,
    C_FOLDER_SETUP_CANCEL_BTN,
    C_FOLDER_SETUP_CONFIRM_BTN,
    C_FOLDER_SETUP_DESCRIPTION,
    C_FOLDER_SETUP_PATH_LABEL,
    C_FOLDER_SETUP_TITLE,
)
from view_models.folder_setup_view_model import FolderSetupViewModel

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class FolderSetupView(tk.Toplevel):
    """Modal dialog shown at first launch when folder_scenarios is unconfigured.

    Passive widget tree bound to FolderSetupViewModel. The user enters a path or
    uses the browse button (which writes path_var directly, equivalent to typing).
    The Presenter owns all validation and persistence logic.

    Attributes:
        _vm: The folder-setup ViewModel driving this dialog.
        _confirm_btn: Submit button whose state mirrors can_confirm_var.
        _view_traces: (var, trace_id) pairs owned by this View, removed on teardown.
    """

    def __init__(self, master: tk.Misc, vm: FolderSetupViewModel) -> None:
        """Build the modal dialog and bind it to *vm*.

        Args:
            master: Tkinter parent (the hidden root window).
            vm: The FolderSetupViewModel that drives this dialog.
        """
        super().__init__(master)
        self._vm = vm
        self._view_traces: list[tuple[tk.Variable, str]] = []

        self.title(C_FOLDER_SETUP_TITLE)
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", vm.cancel)

        self._create_widgets()
        self._center_on_screen()

        vm.bind_close(self.teardown)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build and lay out all dialog widgets."""
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=C_FOLDER_SETUP_DESCRIPTION,
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(frame, text=C_FOLDER_SETUP_PATH_LABEL).pack(anchor="w")

        path_row = ttk.Frame(frame)
        path_row.pack(fill="x", pady=(4, 0))
        ttk.Entry(path_row, textvariable=self._vm.path_var, width=46).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(path_row, text=C_FOLDER_SETUP_BROWSE_BTN, command=self._on_browse).pack(
            side="left", padx=(6, 0)
        )

        ttk.Label(frame, textvariable=self._vm.error_var, foreground="red").pack(
            anchor="w", pady=(6, 0)
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(16, 0))
        ttk.Button(btn_row, text=C_FOLDER_SETUP_CANCEL_BTN, command=self._vm.cancel).pack(
            side="right", padx=(6, 0)
        )
        self._confirm_btn = ttk.Button(
            btn_row, text=C_FOLDER_SETUP_CONFIRM_BTN, command=self._vm.confirm
        )
        self._confirm_btn.pack(side="right")

        # Mirror can_confirm_var onto the confirm button's enabled state.
        self._sync_confirm_state()
        self._view_traces.append(
            (
                self._vm.can_confirm_var,
                self._vm.can_confirm_var.trace_add("write", self._on_can_confirm_changed),
            )
        )

    # ------------------------------------------------------------------
    # Browse handler (View-owned: writes a source Var, like a widget)
    # ------------------------------------------------------------------

    def _on_browse(self) -> None:
        """Open a directory picker and write the selection into path_var."""
        folder = filedialog.askdirectory(title=C_FOLDER_SETUP_TITLE, parent=self)
        if folder:
            self._vm.path_var.set(folder)

    # ------------------------------------------------------------------
    # Derived-state mirror
    # ------------------------------------------------------------------

    def _on_can_confirm_changed(self, *_: object) -> None:
        """Trace callback: re-sync the confirm button state."""
        self._sync_confirm_state()

    def _sync_confirm_state(self) -> None:
        """Apply can_confirm_var to the confirm button's enabled/disabled state."""
        state = "normal" if self._vm.can_confirm_var.get() else "disabled"
        self._confirm_btn.configure(state=state)

    # ------------------------------------------------------------------
    # Layout helper
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Position the dialog at the centre of the primary display."""
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def teardown(self) -> None:
        """Detach View-owned traces, dispose the VM, and destroy the window."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()
        self._vm.dispose()
        self.destroy()


# EOF
