"""Generic button that disables itself and shows a spinning ASCII indicator while a command runs."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from collections.abc import Callable
from typing import Any

from shared.app_global_state import MyButton

_FRAMES = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
_FRAME_MS = 120
_MIN_MS_DEFAULT = 200


class LoadingButton(MyButton):
    """MyButton that disables itself and spins an ASCII indicator while a command runs in a thread.

    The command runs in a daemon thread. Re-enabling and text restoration are posted
    back to the Tk event loop via after(), making them safe regardless of where the
    command finishes.  The loading state is shown for at least *min_ms* milliseconds
    even when the command completes faster.

    Args:
        master: Parent widget.
        text: Button label shown at rest and restored after loading.
        command: Callable executed in a background thread on each click.
        min_ms: Minimum duration (ms) for the loading state; never below 100 ms.
    """

    def __init__(
        self, master: tk.Widget, *, text: str, command: Callable[[], None], min_ms: int = _MIN_MS_DEFAULT, **kwargs: Any
    ) -> None:
        self._original_text = text
        self._threaded_command = command
        self._min_ms = max(min_ms, _MIN_MS_DEFAULT)
        self._frame_idx = 0
        self._spin_id: str | None = None
        super().__init__(master, text=text, command=self._on_click, **kwargs)

    # ------------------------------------------------------------------
    # Internal — click entry point
    # ------------------------------------------------------------------

    def _on_click(self) -> None:
        self._start_loading()
        threading.Thread(target=self._run, daemon=True).start()

    # ------------------------------------------------------------------
    # Internal — loading state
    # ------------------------------------------------------------------

    def _start_loading(self) -> None:
        self._frame_idx = 0
        self.config(state=tk.DISABLED)
        self._tick()

    def _tick(self) -> None:
        self.config(text=_FRAMES[self._frame_idx % len(_FRAMES)])
        self._frame_idx += 1
        self._spin_id = self.after(_FRAME_MS, self._tick)

    def _run(self) -> None:
        t0 = time.monotonic()
        try:
            self._threaded_command()
        finally:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            delay = max(0, self._min_ms - elapsed_ms)
            self.after(delay, self._stop_loading)

    def _stop_loading(self) -> None:
        if self._spin_id is not None:
            self.after_cancel(self._spin_id)
            self._spin_id = None
        self.config(state=tk.NORMAL, text=self._original_text)
