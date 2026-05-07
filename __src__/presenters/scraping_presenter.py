"""Presenter wiring ScrapingPanelView to ScrapingService.

The presenter starts the workflow in a daemon thread, forwards step outcomes
to the view, and exposes cancellation through a threading.Event. No business
logic lives here — only orchestration.

Example:
    >>> presenter = ScrapingPresenter(panel, service)
    >>> presenter.load_provider(provider)
    >>> # The Lancer button in the view then drives the rest.
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging
import threading
from collections.abc import Callable

from models.provider_model import ProviderModel
from services.provider_service import ProviderService
from services.scraping_service import ScrapingService
from views.scraping_panel_view import ScrapingPanelView

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ScrapingPresenter:
    """Orchestrates a scraping workflow between ScrapingPanelView and ScrapingService.

    The workflow runs in a daemon thread so Tkinter's event loop stays responsive.
    Cancellation is signalled to the service via a threading.Event.
    A new provider can be loaded at any time via load_provider(); any running
    workflow is cancelled first.

    Attributes:
        _view: The scraping panel view to update.
        _service: The service that executes Playwright steps.
        _provider: The currently loaded provider model (None when idle).
        _cancel_event: Threading event passed to the service for cancellation.
        _thread: The background worker thread (None when idle).
        is_workflow_active: Optional guard injected from main; returns True when
            a Workflow edit session is already open.

    Example:
        >>> presenter = ScrapingPresenter(panel, service)
        >>> presenter.load_provider(my_provider)
    """

    def __init__(
        self,
        view: ScrapingPanelView,
        service_scraping: ScrapingService,
        service_provider: ProviderService,
        provider: ProviderModel | None = None,
    ) -> None:
        """Initializes the presenter and registers callbacks on the view.

        Args:
            view: The scraping panel view.
            service_scraping: The scraping service that drives Playwright execution.
            provider: Optional initial provider model. Use load_provider() to set
                or change it at runtime.
        """
        self._view = view
        self._service_scraping = service_scraping
        self._service_provider = service_provider
        self._provider: ProviderModel | None = provider
        self._cancel_event = threading.Event()
        self._thread: threading.Thread | None = None

        # pause_event set = running freely; cleared = blocked between steps.
        self._pause_event = threading.Event()
        self._pause_event.set()

        # Guard: returns True when a Workflow edit session is already open.
        self.is_workflow_active: Callable[[], bool] | None = None
        self._logging = logging.getLogger(__name__)

        # Wire view buttons to presenter handlers once at construction time.
        view.set_on_launch(self._on_launch)
        view.set_on_cancel(self._on_cancel)
        view.set_on_pause(self._on_pause)
        view.set_on_resume(self._on_resume)

    def load_provider(self, id_file: str) -> None:
        """Loads a new provider and resets the view for a fresh run.

        If a workflow is currently running it is cancelled before switching.

        Args:
            id_file: The ID of the provider file to load.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> presenter.load_provider("provider_123")
        """
        # Unblock any active pause then cancel the running workflow.

        self._pause_event.set()
        self._cancel_event.set()

        # Update target and clear the stale cancellation signal.
        self._logging.info("Loading provider with id_file={id_file}")
        self._provider = self._service_provider.read_provider(id_file)
        self._cancel_event.clear()

        # Wipe the view and display the new provider's summary.
        self._view.reset()
        self._view.set_provider_info(
            name=self._provider.provider_name,
            url=self._provider.url,
            id_file=self._provider.id_file,
            version=self._provider.version,
        )

    def _on_launch(self) -> None:
        """Starts the workflow in a daemon background thread.

        Returns:
            None.

        Raises:
            None.
        """
        # Guard: do nothing if no provider has been loaded yet.
        if not self._provider:
            self._view.show_warning("Veuillez charger un provider avant de lancer le scraping.")
            return

        # Block launch when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification en cours avant de lancer le scraping."
            )
            return

        # Clear any residual signals from a previous run.
        self._pause_event.set()
        self._cancel_event.clear()
        self._view.set_running_state(True)

        # Use a daemon thread so the app can exit without waiting for the workflow.
        self._thread = threading.Thread(target=self._run_workflow, daemon=True)
        self._thread.start()

    def _on_cancel(self) -> None:
        """Sets the cancel event to abort the running workflow after the current step.

        Returns:
            None.

        Raises:
            None.
        """
        # Unblock any active pause so the cancel signal can be observed immediately.
        self._pause_event.set()
        self._cancel_event.set()

    def _on_pause(self) -> None:
        """Clears the pause event to suspend the workflow before its next step.

        Returns:
            None.

        Raises:
            None.
        """
        # Clearing the event blocks the service loop at the next pause_event.wait().
        self._pause_event.clear()
        self._view.set_paused_state(True)

    def _on_resume(self) -> None:
        """Sets the pause event to resume the suspended workflow.

        Returns:
            None.

        Raises:
            None.
        """
        # Setting the event unblocks the service loop so the next step can execute.
        self._pause_event.set()
        self._view.set_paused_state(False)

    def _on_user_wait_step(self) -> None:
        """Called by the service when a WAIT_USER_ACTION step starts blocking.

        Transitions the view to the paused state so the user sees the
        Reprendre button and knows an action is expected.

        Returns:
            None.

        Raises:
            None.
        """
        # Called from the background thread; set_paused_state is thread-safe.
        self._view.set_paused_state(True)

    def _run_workflow(self) -> None:
        """Thread target: runs the workflow and dispatches the result to the view.

        Returns:
            None.

        Raises:
            None — catastrophic failures are surfaced as a synthetic error report.
        """
        try:
            self._service_scraping.run_workflow(
                self._provider,
                self._cancel_event,
                self._pause_event,
                self._on_user_wait_step,
            )
        except (ValueError, RuntimeError, OSError):
            print("Workflow execution failed with an exception:", exc_info=True)
            ## TODO Push final report bugs

        self._on_workflow_finished()

    def _on_workflow_finished(self) -> None:
        """Restores idle state and displays the final report in the view.

        Args:
            report: The completed ScrapingReportModel to display.

        Returns:
            None.

        Raises:
            None.
        """
        # Ensure pause is cleared so the event is ready for the next run.
        self._pause_event.set()
        # Restore idle button state before rendering the report.
        self._view.set_running_state(False)
