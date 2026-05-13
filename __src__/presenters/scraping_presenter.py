"""Presenter wiring ScrapingView to ScrapingService.

The presenter starts the workflow in a daemon thread, forwards step outcomes
to the view (journal + progress), and exposes cancellation through threading
events. No business logic lives here — only orchestration.

Example:
    >>> presenter = ScrapingPresenter(panel, service_scraping, service_provider)
    >>> presenter.load_provider("abc123")
    >>> # The Lancer button in the view then drives the rest.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import threading
from collections.abc import Callable
from datetime import datetime

from models.provider_model import ProviderModel
from models.scraping_report_model import ScrapingReportModel
from models.step_scraping_model import StepScrapingModel
from repositories.scraping_journal_repository import ScrapingJournalRepository
from services.provider_service import ProviderService
from services.scraping_service import ScrapingService
from shared.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss_fff
from views.scraping_panel_view import ScrapingView

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ScrapingPresenter:
    """Orchestrates a scraping workflow between ScrapingView and ScrapingService.

    The workflow runs in a daemon thread so Tkinter's event loop stays
    responsive. Cancellation is signalled via threading.Event. Provider
    selection is exposed via view callbacks, allowing the user to pick a
    provider from the embedded dropdown without leaving the scraping panel.

    Attributes:
        _view: The scraping panel view.
        _service_scraping: Service that drives Playwright step execution.
        _service_provider: Service for listing and loading providers.
        _provider: Currently loaded provider model.
        _cancel_event: Abort signal passed to the scraping service.
        _pause_event: Pause/resume signal passed to the scraping service.
        _thread: Background worker thread.
        is_workflow_active: Optional guard injected from main; returns True
            when a Workflow edit session is already open.

    Example:
        >>> presenter = ScrapingPresenter(panel, svc_scraping, svc_provider)
        >>> presenter.load_provider("abc123")
    """

    def __init__(
        self,
        view: ScrapingView,
        service_scraping: ScrapingService,
        service_provider: ProviderService,
        journal_repository: ScrapingJournalRepository,
        provider: ProviderModel | None = None,
    ) -> None:
        """Initialize the presenter and register all view callbacks.

        Args:
            view: The scraping panel view.
            service_scraping: Service that executes Playwright workflow steps.
            service_provider: Service for reading and listing providers.
            journal_repository: Repository used to persist journal exports to disk.
            provider: Optional initial provider model.
        """
        self._view = view
        self._service_scraping = service_scraping
        self._service_provider = service_provider
        self._journal_repository = journal_repository
        self._provider: ProviderModel | None = provider
        self._cancel_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._logging = logging.getLogger(__name__)

        # pause_event set = running freely; cleared = blocked between steps.
        self._pause_event = threading.Event()
        self._pause_event.set()

        # Guard: returns True when a Workflow edit session is already open.
        self.is_workflow_active: Callable[[], bool] | None = None

        # Journal entry counter — provides a unique iid for each Treeview row.
        self._journal_entry_counter: int = 0
        self._current_journal_item_id: str | None = None

        self._providers_loaded: bool = False

        # Wire all view callbacks to presenter handlers.
        self._wire_view_callbacks()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_providers_loaded(self) -> None:
        """Populate the provider dropdown on first show, skipped if already loaded."""
        if not self._providers_loaded:
            self._on_refresh_providers()

    def load_provider(self, id_file: str) -> None:
        """Load a provider by id_file and reset the view for a fresh run.

        If a workflow is currently running it is cancelled before switching.

        Args:
            id_file: The ID of the provider file to load.
        """
        # Unblock any active pause, then cancel the running workflow.
        self._pause_event.set()
        self._cancel_event.set()

        # Load the new provider and clear the stale cancellation signal.
        self._logging.info("Loading provider id_file=%s", id_file)
        self._provider = self._service_provider.read_provider(id_file)
        self._cancel_event.clear()

        # Ensure the provider dropdown is populated before selecting.
        self.ensure_providers_loaded()

        # Refresh the view provider selection and reset run-specific state.
        self._view.set_selected_provider(id_file)
        self._view.reset()

    # ------------------------------------------------------------------
    # View callback wiring
    # ------------------------------------------------------------------

    def _wire_view_callbacks(self) -> None:
        """Register all presenter handlers on the view.

        Returns:
            None.
        """
        self._view.set_on_launch(self._on_launch)
        self._view.set_on_cancel(self._on_cancel)
        self._view.set_on_pause(self._on_pause)
        self._view.set_on_resume(self._on_resume)
        self._view.set_on_provider_selected(self._on_provider_selected)
        self._view.set_on_refresh_providers(self._on_refresh_providers)
        self._view.set_on_export_journal(self._on_export_journal)

    # ------------------------------------------------------------------
    # Provider management callbacks
    # ------------------------------------------------------------------

    def _on_export_journal(self, path: str) -> None:
        """Retrieve journal rows from the view and persist them via the repository.

        Args:
            path: Absolute path of the destination file chosen by the user.
        """
        try:
            rows = self._view.get_journal_rows()
            self._journal_repository.save(path, rows)
        except OSError as exc:
            self._logging.error("Journal export failed: %s", exc)
            self._view.show_warning(f"Impossible d'écrire le fichier :\n{exc}")

    def _on_provider_selected(self, id_file: str) -> None:
        """Load the provider chosen from the view's dropdown.

        Args:
            id_file: Unique file identifier of the selected provider.
        """
        # Guard: block provider switch while a workflow edit session is open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification avant de changer de fournisseur."
            )
            return

        self._logging.info("Provider selected from view: id_file=%s", id_file)
        self.load_provider(id_file)

    def _on_refresh_providers(self) -> None:
        """Reload the providers list and forward it to the view dropdown."""
        try:
            providers = self._service_provider.list_all_providers()
        except Exception as exc:  # noqa: BLE001
            self._logging.error("Failed to load providers list: %s", exc)
            providers = []
        self._providers_loaded = True

        # Build display-ready dicts and push to the view.
        rows = [
            {
                "id_file": p.id_file,
                "provider_name": p.provider_name,
                "url": p.url,
                "version": p.version,
                "modified_date": p.modified_date,
            }
            for p in providers
        ]
        self._view.render_providers_list(rows)

    # ------------------------------------------------------------------
    # Workflow control callbacks
    # ------------------------------------------------------------------

    def _on_launch(self) -> None:
        """Start the workflow in a daemon background thread.

        Returns:
            None.
        """
        if not self._provider:
            self._view.show_warning("Veuillez charger un fournisseur avant de lancer le scraping.")
            return

        # Block launch when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification avant de lancer le scraping."
            )
            return

        # Reset signals and journal counter from any previous run.
        self._pause_event.set()
        self._cancel_event.clear()
        self._journal_entry_counter = 0
        self._current_journal_item_id = None
        self._view.set_running_state(True)

        started_at = datetime.now()
        self._view.start_elapsed_timer(started_at)

        # Collect URL source selection from the view before spawning the thread.
        url_source = self._view.get_url_source()
        source_type: str = url_source["type"]
        source_value: list[str] | str = url_source["value"]

        # Launch workflow in a daemon thread so the UI stays responsive.
        self._thread = threading.Thread(
            target=self._run_workflow,
            args=(source_type, source_value),
            daemon=True,
        )
        self._thread.start()

    def _on_cancel(self) -> None:
        """Signal the running workflow to abort after the current step.

        Returns:
            None.
        """
        # Unblock any pause so the cancel signal is observed immediately.
        self._pause_event.set()
        self._cancel_event.set()

    def _on_pause(self) -> None:
        """Suspend the workflow before its next step.

        Returns:
            None.
        """
        self._pause_event.clear()
        self._view.set_paused_state(True)

    def _on_resume(self) -> None:
        """Resume a suspended workflow.

        Returns:
            None.
        """
        self._pause_event.set()
        self._view.set_paused_state(False)

    def _on_user_wait_step(self) -> None:
        """Called by the service when a WAIT_USER_ACTION step starts blocking.

        Transitions the view to the paused state so the user sees the
        Reprendre button and knows manual action is expected.
        """
        # Called from the background thread; set_paused_state is thread-safe.
        self._view.set_paused_state(True)

    # ------------------------------------------------------------------
    # Step lifecycle callbacks
    # ------------------------------------------------------------------

    def _on_step_start(self, step: StepScrapingModel) -> None:
        """Called by the service just before a step executes.

        Inserts a pending row in the journal so the user sees the step
        name immediately, before the result is known.

        Args:
            step: The step model about to execute.
        """
        self._journal_entry_counter += 1
        item_id = f"entry_{self._journal_entry_counter}"
        self._current_journal_item_id = item_id

        # Pre-insert the journal row with a 'pending' placeholder.
        date_str = get_datetime_now_yyyy_mm_dd_hh_mm_ss_fff()
        self._view.start_journal_entry(item_id, date_str, step.step_type.value)

    def _on_step_done(
        self,
        step: StepScrapingModel,
        success: bool,
        message: str,
        elapsed_s: float,
    ) -> None:
        """Called by the service after each step completes.

        Updates the pre-inserted journal row and refreshes the progress frame.

        Args:
            step: The completed step model.
            success: True when the step produced no error.
            message: Short result message from the executor.
            elapsed_s: Wall-clock duration of the step in seconds.
        """
        # Complete the journal row started in _on_step_start.
        if self._current_journal_item_id:
            self._view.complete_journal_entry(
                item_id=self._current_journal_item_id,
                msg_step_ended=message,
                success=success,
                duration_s=elapsed_s,
            )

        # Push live progress values to the progression frame.
        url, tabs = self._service_scraping.get_page_info()
        last_result = f"{'OK' if success else 'ERREUR'} — {message}"
        self._view.update_progress(
            url=url,
            tabs=tabs,
            current_step=step.step_type.value,
            last_result=last_result,
            status="en cours",
            stats=self._service_scraping.current_stats,
        )

    def _on_init_step(self, message: str) -> None:
        """Called by the service during browser initialization phases.

        Args:
            message: Human-readable init status string.
        """
        self._view.update_progress(
            url="",
            tabs=0,
            current_step=message,
            last_result="",
            status="en cours",
            stats={"success": 0, "errors": 0, "clicks": 0, "urls": 0},
        )

    # ------------------------------------------------------------------
    # Workflow thread target
    # ------------------------------------------------------------------

    def _run_workflow(self, url_source_type: str, url_source_value: list[str] | str) -> None:
        """Thread target: run the workflow and dispatch the result to the view.

        Args:
            url_source_type: URL source type string (``"manual"``, ``"csv"``,
                ``"folder"``, or ``""`` when no source is configured).
            url_source_value: Matching value — list of URLs or path string.

        Returns:
            None.

        Raises:
            None — catastrophic failures are logged and result in a None report.
        """
        report: ScrapingReportModel | None = None
        try:
            report = self._service_scraping.run_workflow(
                self._provider,
                url_source_type,
                url_source_value,
                self._cancel_event,
                self._pause_event,
                self._on_user_wait_step,
                self._on_step_start,
                self._on_step_done,
                self._on_init_step,
            )
        except (ValueError, RuntimeError, OSError) as exc:
            self._logging.exception("Workflow execution failed: %s", exc)

        self._on_workflow_finished(report)

    def _on_workflow_finished(self, report: ScrapingReportModel | None) -> None:
        """Restore idle state and display the final report in the view.

        Args:
            report: Completed report, or None when the run raised an exception.
        """
        # Ensure pause is released so the event is ready for the next run.
        self._pause_event.set()
        self._view.stop_elapsed_timer()
        self._view.set_running_state(False)

        # Push final status and statistics to the progression frame.
        if report is not None:
            status = "annulé" if report.cancelled else "terminé"
            self._view.update_progress(
                url="",
                tabs=0,
                current_step="—",
                last_result="Workflow terminé.",
                status=status,
                stats={
                    "success": report.steps_success,
                    "errors": report.steps_failed,
                    "clicks": report.clicks_performed,
                    "urls": report.urls_opened,
                },
            )
        else:
            self._view.update_progress(
                url="",
                tabs=0,
                current_step="—",
                last_result="Erreur critique — voir les logs.",
                status="erreur",
                stats={"success": 0, "errors": 0, "clicks": 0, "urls": 0},
            )
