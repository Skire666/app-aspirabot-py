"""Base class shared by all ViewModels.

Provides tracked trace registration, a re-entrant/suspendable recompute gate,
change-guarded Var writes, debounced scheduling, a threading proxy, and
deterministic disposal.  Subclasses override ``_recompute_derived`` and never
manage trace ids, re-entrancy flags, or pending ``after`` calls themselves.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress

# -----------------------------------------------------------------------------
# Base class
# -----------------------------------------------------------------------------


class ViewModelBase:
    """Infrastructure shared by all ViewModels.

    Provides tracked trace registration, a re-entrant/suspendable recompute
    gate, change-guarded Var writes, debounced scheduling, and deterministic
    disposal.  Subclasses override ``_recompute_derived`` and never manage
    trace ids, re-entrancy flags, or pending ``after`` calls themselves.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise the base infrastructure.

        Args:
            master: Real Tk root or widget; Vars and after() scheduling are
                anchored to it.  Must be the first call in every subclass
                ``__init__``.
        """
        # Real Tk root/widget; Vars and after() scheduling are anchored to it.
        self._master = master
        # (var, trace_id) pairs registered through _register_trace, for disposal.
        self._trace_ids: list[tuple[tk.Variable, str]] = []
        # Pending debounced callbacks, keyed by a stable string.
        self._after_ids: dict[str, str] = {}
        # >0 while a batch_update is active: recompute is deferred.
        self._suspend_depth: int = 0
        # True while inside _recompute_derived: blocks re-entrant recompute.
        self._in_recompute: bool = False

    # ----- Trace registration (always tracked for disposal) -----

    def _register_trace(self, var: tk.Variable, callback: Callable[..., None]) -> None:
        """Add a write-trace on *var* and remember its id for later removal.

        Args:
            var: Tkinter Var to watch.
            callback: Callable invoked on every write to *var*.
        """
        trace_id = var.trace_add("write", callback)
        self._trace_ids.append((var, trace_id))

    # ----- Guarded Var write -----

    @staticmethod
    def _set_if_changed(var: tk.Variable, value: object) -> None:
        """Write *value* into *var* only when it differs from the current value.

        Args:
            var: Target Var.
            value: New value to apply.
        """
        if var.get() != value:  # pyright: ignore[reportUnknownMemberType]
            var.set(value)  # pyright: ignore[reportUnknownMemberType]

    # ----- Recompute gate -----

    def _guarded_recompute(self, *_: object) -> None:
        """Single entry point for derived-state recomputation.

        No-op while a batch update is active or while already recomputing.
        """
        if self._suspend_depth > 0 or self._in_recompute:
            return
        self._in_recompute = True
        try:
            self._recompute_derived()
        finally:
            self._in_recompute = False

    def _recompute_derived(self) -> None:
        """Recompute all derived Vars.

        Overridden by subclasses; no-op by default.  Only called through
        ``_guarded_recompute`` — never invoked directly.
        """

    @contextmanager
    def batch_update(self) -> Iterator[None]:
        """Suspend recomputation for a block of Var writes; recompute once on exit.

        Used by the Presenter when populating several source Vars at once (e.g.
        on load) so derived state is computed a single time instead of once per
        write.
        """
        self._suspend_depth += 1
        try:
            yield
        finally:
            self._suspend_depth -= 1
            if self._suspend_depth == 0:
                self._guarded_recompute()

    # ----- Debounced scheduling -----

    def _schedule(self, key: str, delay_ms: int, callback: Callable[[], None]) -> None:
        """Debounce *callback* under *key*: a new call cancels the pending one.

        Args:
            key: Stable identifier grouping calls that should cancel each other.
            delay_ms: Delay in milliseconds before *callback* fires.
            callback: Zero-argument callable to invoke after the delay.
        """
        pending = self._after_ids.get(key)
        if pending is not None:
            self._master.after_cancel(pending)
        self._after_ids[key] = self._master.after(
            delay_ms, lambda: self._run_scheduled(key, callback)
        )

    def _run_scheduled(self, key: str, callback: Callable[[], None]) -> None:
        """Clear the pending id for *key* then run *callback*.

        Args:
            key: Identifier to remove from the pending dict.
            callback: Zero-argument callable to invoke.
        """
        self._after_ids.pop(key, None)
        callback()

    # ----- Threading proxy -----

    def after(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """Schedule *callback* on the main Tkinter thread after *delay_ms* ms.

        Allows Presenters to post UI-thread work from background threads without
        importing ``tkinter`` directly.

        Args:
            delay_ms: Delay in milliseconds before *callback* fires.
            callback: Zero-argument callable to schedule.
        """
        self._master.after(delay_ms, callback)

    # ----- Disposal -----

    def dispose(self) -> None:
        """Remove every registered trace and cancel every pending after-call.

        Must be called by whoever owns the VM lifecycle when the View is
        discarded (app shutdown, dialog close, tab destroy).  Idempotent.
        """
        for var, trace_id in self._trace_ids:
            with suppress(Exception):
                var.trace_remove("write", trace_id)
        self._trace_ids.clear()
        for after_id in self._after_ids.values():
            with suppress(Exception):
                self._master.after_cancel(after_id)
        self._after_ids.clear()


# EOF
