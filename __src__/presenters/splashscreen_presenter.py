"""Presenter orchestrating the splash screen startup sequence."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import traceback
from collections.abc import Callable

from services.startup_service import StartupService
from shared.constants import (
    C_SPLASHSCREEN_DISPLAY_MS_BY_STEP,
    C_SPLASHSCREEN_DISPLAY_MS_TOTAL,
    C_SPLASHSCREEN_STEP_LABELS,
)
from shared.exception_util import AspirabotBaseError
from view_models.splashscreen_view_model import SplashscreenViewModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class SplashscreenPresenter:
    """Drives the three-step startup sequence displayed on the splash screen.

    Each step is scheduled via Tkinter's after() so the main event loop
    remains unblocked. On success the splash is destroyed and on_success
    is called; on failure an error dialog is shown and on_failure is called.

    Attributes:
        _view: The splash screen Toplevel window.
        _service: Service executing the three initialization steps.
        _on_success: Callback invoked when all steps complete without error.
        _on_failure: Callback invoked when any step raises an exception.
    """

    def __init__(
        self,
        vm: SplashscreenViewModel,
        service: StartupService,
        on_success: Callable[[], None],
        on_failure: Callable[[], None],
    ) -> None:
        """Initialize the presenter with its ViewModel, service, and outcome callbacks.

        Args:
            vm: The splash screen ViewModel.
            service: The startup service exposing the three init step methods.
            on_success: Called after all three steps succeed and the splash closes.
            on_failure: Called after any step fails and the splash closes.
        """
        self._vm = vm
        self._service = service
        self._on_success = on_success
        self._on_failure = on_failure

    # -----------------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------------

    def start(self) -> None:
        """Schedule step 1 to run as soon as the event loop processes it.

        Call this once after constructing the presenter, before mainloop().
        """
        # after(0) defers execution to the next event-loop cycle so the
        # splash window is fully painted before the first step runs.
        self._vm.after(0, self._run_step_1)

    # -----------------------------------------------------------------------------
    # Startup steps
    # -----------------------------------------------------------------------------

    def _run_step_1(self) -> None:
        """Execute step 1: load configuration from persistent storage."""
        self._vm.status_var.set(C_SPLASHSCREEN_STEP_LABELS[0])
        try:
            self._service.load_configuration()
            self._vm.after(C_SPLASHSCREEN_DISPLAY_MS_BY_STEP, self._run_step_2)
        except AspirabotBaseError as exc:
            self._handle_error(str(exc))

    def _run_step_2(self) -> None:
        """Execute step 2: create required application directories."""
        self._vm.status_var.set(C_SPLASHSCREEN_STEP_LABELS[1])
        try:
            self._service.create_required_directories()
            self._vm.after(C_SPLASHSCREEN_DISPLAY_MS_BY_STEP, self._run_step_3)
        except AspirabotBaseError as exc:
            traceback.print_stack()
            self._handle_error(str(exc))

    def _run_step_3(self) -> None:
        """Execute step 3: initialize the rotating-file logging system."""
        self._vm.status_var.set(C_SPLASHSCREEN_STEP_LABELS[2])
        try:
            self._service.initialize_logging()
            self._vm.after(C_SPLASHSCREEN_DISPLAY_MS_BY_STEP, self._run_step_4)
        except AspirabotBaseError as exc:
            self._handle_error(str(exc))

    def _run_step_4(self) -> None:
        """Final step: ensure minimum display time, then trigger the success callback."""
        self._vm.status_var.set(C_SPLASHSCREEN_STEP_LABELS[3])
        try:
            elapsed_ms = self._service.get_time_elapsed_when_booting()
            remaining_ms = max(0, C_SPLASHSCREEN_DISPLAY_MS_TOTAL - elapsed_ms)
            self._vm.after(int(remaining_ms), self._on_startup_complete)
        except AspirabotBaseError as exc:
            self._handle_error(str(exc))

    # -----------------------------------------------------------------------------
    # Outcome handlers
    # -----------------------------------------------------------------------------

    def _on_startup_complete(self) -> None:
        """Destroy the splash screen and trigger the success callback."""
        self._vm.destroy()
        self._on_success()

    def _handle_error(self, message: str) -> None:
        """Show a blocking error dialog, then abort startup.

        Args:
            message: Human-readable description of the failure cause.
        """
        self._vm.show_error(message)
        self._vm.destroy()
        self._on_failure()


# EOF
