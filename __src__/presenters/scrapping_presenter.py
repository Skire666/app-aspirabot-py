"""Presenter wiring ScrappingPanelView to ScrappingService.

The presenter starts the workflow in a daemon thread, forwards step outcomes
to the view, and exposes cancellation through a threading.Event. No business
logic lives here — only orchestration.

Example:
    >>> presenter = ScrappingPresenter(panel, service)
    >>> presenter.load_provider(provider)
    >>> # The Lancer button in the view then drives the rest.
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import threading
from datetime import datetime

from models.provider_model import DATETIME_FORMAT, ProviderModel
from models.scrapping_report_model import ScrappingReportModel, StepResultModel
from models.step_scrapping_model import StepScrappingModel
from services.scrapping_service import ScrappingService
from views.scrapping_panel_view import ScrappingPanelView

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ScrappingPresenter:
    """Orchestrates a scraping workflow between ScrappingPanelView and ScrappingService.

    The workflow runs in a daemon thread so Tkinter's event loop stays responsive.
    Cancellation is signalled to the service via a threading.Event.
    A new provider can be loaded at any time via load_provider(); any running
    workflow is cancelled first.

    Attributes:
        _view: The scrapping panel view to update.
        _service: The service that executes Playwright steps.
        _provider: The currently loaded provider model (None when idle).
        _cancel_event: Threading event passed to the service for cancellation.
        _thread: The background worker thread (None when idle).

    Example:
        >>> presenter = ScrappingPresenter(panel, service)
        >>> presenter.load_provider(my_provider)
    """

    def __init__(
        self,
        view: ScrappingPanelView,
        service: ScrappingService,
        provider: ProviderModel | None = None,
    ) -> None:
        """Initializes the presenter and registers callbacks on the view.

        Args:
            view: The scrapping panel view.
            service: The scrapping service that drives Playwright execution.
            provider: Optional initial provider model. Use load_provider() to set
                or change it at runtime.
        """
        self._view = view
        self._service = service
        self._provider: ProviderModel | None = provider
        self._cancel_event = threading.Event()
        self._thread: threading.Thread | None = None

        # Wire view buttons to presenter handlers once at construction time.
        view.set_on_launch(self._on_launch)
        view.set_on_cancel(self._on_cancel)

    def load_provider(self, provider: ProviderModel) -> None:
        """Loads a new provider and resets the view for a fresh run.

        If a workflow is currently running it is cancelled before switching.

        Args:
            provider: The provider whose workflow will be executed on next launch.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> presenter.load_provider(provider)
        """
        # Stop any in-progress run before replacing the provider.
        self._cancel_event.set()

        # Update target and clear the stale cancellation signal.
        self._provider = provider
        self._cancel_event.clear()

        # Wipe the view and display the new provider's summary.
        self._view.reset()
        self._view.set_provider_info(
            name=provider.provider_name,
            url=provider.url,
            id_file=provider.id_file,
            version=provider.version,
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
            return

        # Clear any residual cancellation signal from a previous run.
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
        # The service polls this event before each step and exits the loop when set.
        self._cancel_event.set()

    def _run_workflow(self) -> None:
        """Thread target: runs the workflow and dispatches the result to the view.

        Returns:
            None.

        Raises:
            None — catastrophic failures are surfaced as a synthetic error report.
        """
        try:
            report = self._service.run_workflow(
                self._provider,
                self._on_step_done,
                self._cancel_event,
            )
        except (ValueError, RuntimeError, OSError) as exc:
            report = self._build_error_report(str(exc))

        self._on_workflow_finished(report)

    def _on_step_done(
        self,
        index: int,
        step: StepScrappingModel,
        success: bool,
        message: str,
        time_elapsed: float,
    ) -> None:
        """Forwards a completed step result to the view.

        Called by the service from the background thread; all view calls are
        safe because they schedule updates via self.after(0, ...).

        Args:
            index: Zero-based position of the step.
            step: The step that was executed.
            success: True when the step completed without error.
            message: Outcome or error description.
            time_elapsed: Duration of the step execution in seconds.

        Returns:
            None.

        Raises:
            None.
        """
        total = len(self._provider.steps)
        step_type = step.step_type.value

        # Update the progress indicator then append the result to the log below.
        self._view.show_step_progress(index, total, step_type)
        self._view.append_step_result(index, step_type, success, message, time_elapsed)

    def _on_workflow_finished(self, report: ScrappingReportModel) -> None:
        """Restores idle state and displays the final report in the view.

        Args:
            report: The completed ScrappingReportModel to display.

        Returns:
            None.

        Raises:
            None.
        """
        # Restore idle button state before rendering the report.
        self._view.set_running_state(False)
        self._view.show_report(report)

    def _build_error_report(self, error_message: str) -> ScrappingReportModel:
        """Creates a synthetic report when the workflow fails catastrophically.

        Args:
            error_message: Description of the fatal exception.

        Returns:
            A ScrappingReportModel that reflects the failure.

        Raises:
            None.
        """
        now = datetime.now().strftime(DATETIME_FORMAT)

        # Represent the fatal failure as a single failed step at index 0.
        return ScrappingReportModel(
            provider_name=self._provider.provider_name if self._provider else "N/A",
            total_steps=len(self._provider.steps) if self._provider else 0,
            steps_done=0,
            steps_failed=1,
            cancelled=False,
            started_at=now,
            finished_at=now,
            step_results=[StepResultModel(0, "N/A", False, error_message, time_elapsed=0.0)],
        )
