"""Extra tests for throttling.py — covering the branches missed by test_throttling.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from views.components.drag_drop_list.utils.throttling import Debouncer


class TestDebouncerScheduleWithExistingJob:
    def test_cancels_previous_job_before_scheduling(self) -> None:
        debouncer = Debouncer(100)
        widget = MagicMock()
        widget.after.return_value = "job_1"

        # First schedule — sets _job to "job_1"
        debouncer.schedule(widget, lambda: None)
        assert debouncer._job == "job_1"

        widget.after.return_value = "job_2"
        debouncer.schedule(widget, lambda: None)

        # after_cancel must have been called with the old job
        widget.after_cancel.assert_called_with("job_1")
        assert debouncer._job == "job_2"


class TestDebouncerCancel:
    def test_cancel_with_pending_job(self) -> None:
        debouncer = Debouncer(100)
        widget = MagicMock()
        widget.after.return_value = "job_1"
        debouncer.schedule(widget, lambda: None)

        debouncer.cancel(widget)

        widget.after_cancel.assert_called_with("job_1")
        assert debouncer._job is None
        assert not debouncer.pending

    def test_cancel_without_pending_no_op(self) -> None:
        debouncer = Debouncer(100)
        widget = MagicMock()
        debouncer.cancel(widget)  # should not raise
        widget.after_cancel.assert_not_called()


class TestDebouncerWrapClearsJob:
    def test_wrapped_callback_clears_job_then_calls_callback(self) -> None:
        debouncer = Debouncer(0)
        widget = MagicMock()
        widget.after.return_value = "job_x"

        called: list[bool] = []
        debouncer.schedule(widget, lambda: called.append(True))

        # Extract the wrapped callback from the after() call
        wrapped = widget.after.call_args[0][1]
        assert debouncer._job == "job_x"

        # Fire the wrapped callback
        wrapped()

        assert debouncer._job is None
        assert called == [True]
