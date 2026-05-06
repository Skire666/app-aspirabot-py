"""Reusable debouncer and throttler utilities for UI rate-limiting."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


class Debouncer:
    """Delays a callback until a quiescence period has elapsed.

    Each schedule() call resets the timer. The callback fires only
    after `delay_ms` milliseconds of inactivity.

    Example:
        >>> d = Debouncer(delay_ms=200)
        >>> d.schedule(widget, my_callback)
    """

    def __init__(self, delay_ms: int) -> None:
        """Initializes the debouncer with a delay.

        Args:
            delay_ms: Milliseconds of inactivity before firing.
        """
        self._delay_ms: int = max(0, delay_ms)
        self._job: str | None = None

    # ── Public API ───────────────────────────────────────────────────

    def schedule(self, widget: Any, callback: Callable[[], None]) -> None:
        """Schedules callback; cancels any previously pending call.

        Args:
            widget: A tkinter widget used for after() scheduling.
            callback: Zero-argument callable to fire after delay.
        """
        if self._job is not None:
            widget.after_cancel(self._job)
        self._job = widget.after(self._delay_ms, self._wrap(callback))

    def cancel(self, widget: Any) -> None:
        """Cancels any pending callback.

        Args:
            widget: The same tkinter widget used in schedule().
        """
        if self._job is not None:
            widget.after_cancel(self._job)
            self._job = None

    @property
    def pending(self) -> bool:
        """True when a callback is scheduled but has not fired."""
        return self._job is not None

    # ── Private helpers ──────────────────────────────────────────────

    def _wrap(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Wraps callback to clear the job handle on fire."""
        def _inner() -> None:
            self._job = None
            callback()
        return _inner


class Throttler:
    """Allows a callback at most once per interval.

    Unlike Debouncer, Throttler returns False from should_allow()
    within the cooldown window without queuing future calls.

    Example:
        >>> t = Throttler(interval_ms=16)
        >>> if t.should_allow():
        ...     redraw()
    """

    def __init__(self, interval_ms: int) -> None:
        """Initializes the throttler.

        Args:
            interval_ms: Minimum milliseconds between allowed calls.
        """
        self._interval_ms: int = max(0, interval_ms)
        self._last_ts: float = 0.0

    def should_allow(self) -> bool:
        """Returns True if enough time has passed to allow the action.

        Side-effect: records the current timestamp when True.

        Returns:
            True when the action should proceed, False when throttled.
        """
        if self._interval_ms <= 0:
            return True
        now = time.perf_counter() * 1000.0
        if now - self._last_ts >= self._interval_ms:
            self._last_ts = now
            return True
        return False

    def reset(self) -> None:
        """Resets the throttle window, allowing the next call immediately."""
        self._last_ts = 0.0
