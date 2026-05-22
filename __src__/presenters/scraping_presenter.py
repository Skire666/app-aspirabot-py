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
from pathlib import Path

from models.launch_profile_model import LaunchProfileModel
from models.provider_model import ProviderModel
from models.scraping_context_model import ScrapingContextModel
from models.scraping_report_model import ScrapingReportModel
from models.step_scraping_model import StepScrapingModel
from services.provider_service import ProviderService
from services.scraping_service import ScrapingService
from shared.datetime_util import (
    get_time_now_hh_mm_ss,
    get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff,
)
from shared.enums import EventScrapingEnum, OpenUrlModeEnum, StepTypeEnum
from shared.exception_util import AspirabotError
from shared.i18n_fra import (
    C_SCRAPING_EMERGENCY_STOP_INVALID_MSG,
    C_SCRAPING_EVENT_BROWSER_INIT,
    C_SCRAPING_EVENT_CONTEXT_INIT,
    C_SCRAPING_EVENT_WORKFLOW_INIT,
    C_SCRAPING_EXPORT_WRITE_ERROR,
    C_SCRAPING_JOURNAL_PENDING_STATUS,
    C_SCRAPING_JOURNAL_RESULT_ERROR,
    C_SCRAPING_JOURNAL_RESULT_OK,
    C_SCRAPING_NO_PROVIDER_LOADED,
    C_SCRAPING_STATUS_CANCELLED,
    C_SCRAPING_STATUS_EMERGENCY_STOP,
    C_SCRAPING_STATUS_ERROR,
    C_SCRAPING_STATUS_FINISHED,
    C_SCRAPING_WORKFLOW_ACTIVE_LAUNCH,
    C_SCRAPING_WORKFLOW_ACTIVE_PROVIDER,
)
from shared.operating_system_util import open_folder
from views.scraping_view import ScrapingView, ScrapingViewCallbacks
from views.steps.open_url_form_def import C_KEY_URL_MODE

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
        provider: ProviderModel | None = None,
    ) -> None:
        """Initialize the presenter and register all view callbacks.

        Args:
            view: The scraping panel view.
            service_scraping: Service that executes Playwright workflow steps and journal exports.
            service_provider: Service for reading and listing providers.
            provider: Optional initial provider model.
        """
        self._view = view
        self._service_scraping = service_scraping
        self._service_provider = service_provider
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
        self._all_logs_scraping: list[str] = []

        self._last_loaded: datetime | None = None

        # Captured at launch time (main thread) to avoid cross-thread Tkinter access.
        self._emergency_stop_threshold: int = 0

        # Tracks whether the launch-profile form has unsaved changes.
        self._is_profile_dirty: bool = False

        # Wire all view callbacks to presenter handlers.
        self._wire_view_callbacks()

    # ------------------------------------------------------------------
    # Public API — providers
    # ------------------------------------------------------------------

    def ensure_scenarios_loaded(self) -> None:
        """Populate the provider dropdown on first show, skipped if already loaded."""
        # Skip reload when data is still fresh (within the 1-second window).
        if self._last_loaded and (datetime.now() - self._last_loaded).total_seconds() <= 1:
            return
        self._on_refresh_scenarios()

    def load_profile(self, id_profile: str) -> None:
        """Select and apply a specific profile by ID in the view.

        Args:
            id_profile: The id_profile to select and apply.
                Expects load_provider() to have been called first.
        """
        if not self._provider:
            return

        # Select the profile in the list then apply its values to the form.
        self._view.set_selected_profile(id_profile)
        self._on_profile_selected(id_profile)

    def load_provider(self, id_file: str) -> None:
        """Load a provider by id_file and reset the view for a fresh run.

        If a workflow is currently running it is cancelled before switching.

        Args:
            id_file: The ID of the provider file to load.
        """
        # Abort any in-progress run before swapping the provider.
        self._cancel_active_run()

        self._logging.info("Loading provider id_file=%s", id_file)
        self._provider = self._service_provider.read_provider(id_file)
        self._cancel_event.clear()

        # Guarantee at least one profile exists, then populate the view.
        self._ensure_default_profile()
        self.ensure_scenarios_loaded()
        self._setup_view_after_load(id_file)

    # ------------------------------------------------------------------
    # Private helpers — provider loading
    # ------------------------------------------------------------------

    def _cancel_active_run(self) -> None:
        """Unblock any active pause and signal the running workflow to stop."""
        self._pause_event.set()
        self._cancel_event.set()

    def _ensure_default_profile(self) -> None:
        """Add and persist a default profile when the provider has none."""
        if not self._provider.launch_profiles:
            self._provider.launch_profiles.append(LaunchProfileModel.get_default())
            self._service_provider.update_provider(self._provider)

    def _setup_view_after_load(self, id_file: str) -> None:
        """Reset the view, populate profiles, and seed the date label.

        Args:
            id_file: ID of the newly loaded provider, forwarded to the dropdown.
        """
        # Select the provider in the dropdown and clear stale run state.
        self._view.set_selected_provider(id_file)
        self._view.reset()

        # Unlock the profiles frame and populate it from the loaded provider.
        self._view.set_profile_management_enabled(True)
        self._refresh_profiles_list()
        self._load_last_used_profile()

        # Seed the date label with the provider file's current modification date.
        self._view.set_profile_modified_date(self._provider.modified_date_provider)

    # ------------------------------------------------------------------
    # View callback wiring
    # ------------------------------------------------------------------

    def _wire_view_callbacks(self) -> None:
        """Register all presenter handlers on the view.

        Returns:
            None.
        """
        self._view.bind_callbacks(
            ScrapingViewCallbacks(
                on_launch=self._on_launch,
                on_cancel=self._on_cancel,
                on_pause=self._on_pause,
                on_resume=self._on_resume,
                on_provider_selected=self._on_provider_selected,
                on_refresh_scenarios=self._on_refresh_scenarios,
                on_profile_selected=self._on_profile_selected,
                on_profile_new=self._on_profile_new,
                on_profile_delete=self._on_profile_delete,
                on_profile_rename=self._on_profile_rename,
                on_profile_save=self._on_profile_save,
                on_form_changed=self._on_form_changed,
                on_manual_urls_confirmed=self._on_manual_urls_confirmed,
                on_open_export_folder=self._on_open_export_folder,
                on_export_journal=self._on_export_journal,
            )
        )

    # ------------------------------------------------------------------
    # Provider management callbacks
    # ------------------------------------------------------------------

    def _on_export_journal(self, path: str) -> None:
        """Retrieve journal rows and persist them via the scraping service.

        Args:
            path: Absolute path of the destination file chosen by the user.
        """
        try:
            rows = self._all_logs_scraping
            self._service_scraping.export_journal(path, rows)
        except OSError as exc:
            self._logging.exception("Échec de l'export du journal")
            self._view.show_warning(C_SCRAPING_EXPORT_WRITE_ERROR.format(exc=exc))

    def _on_provider_selected(self, id_file: str) -> None:
        """Load the provider chosen from the view's dropdown.

        Args:
            id_file: Unique file identifier of the selected provider.
        """
        # Guard: block provider switch while a workflow edit session is open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(C_SCRAPING_WORKFLOW_ACTIVE_PROVIDER)
            return

        self._logging.info("Provider selected from view: id_file=%s", id_file)
        self.load_provider(id_file)

    def _on_refresh_scenarios(self) -> None:
        """Reload the providers list and forward it to the view dropdown."""
        try:
            providers: list[ProviderModel] = self._service_provider.list_all_scenarios()
        except AspirabotError, OSError:
            self._logging.exception("Échec du chargement de la liste des providers")
            providers = []

        # Build display-ready dicts and push to the view.
        rows: list[dict[str, str]] = [
            {
                "id_file": p.id_file,
                "provider_name": p.provider_name,
                "provider_desc": p.provider_desc,
                "version": p.version,
                "modified_date": str(p.modified_date_provider),
            }
            for p in providers
        ]
        self._view.render_providers_list(rows)
        self._last_loaded = datetime.now()

    # ------------------------------------------------------------------
    # Profile management callbacks
    # ------------------------------------------------------------------

    def _on_profile_selected(self, id_profile: str) -> None:
        """Apply the selected profile to the launch profile form.

        Args:
            id_profile: Unique identifier of the profile to restore.
        """
        profile = self._find_profile(id_profile)
        if profile is None:
            return

        # Restore form values, then reset dirty state and enable the section.
        self._view.set_export_folder(profile.export_folder)
        self._view.set_url_source(profile.url_source_type, profile.url_source_value)
        self._view.set_emergency_stop_threshold(profile.emergency_stop_threshold)
        self._view.set_launch_profile_enabled(True)
        self._is_profile_dirty = False

        # Enable rename/save and display the provider file's last modification date.
        self._view.set_rename_profile_button_state(True)
        self._view.set_save_profile_button_state(True)
        self._view.set_profile_modified_date(self._provider.modified_date_provider)

    def _on_profile_new(self, name: str) -> None:
        """Create a new named profile, persist it and select it in the view.

        Args:
            name: Profile name entered by the user.

        Returns:
            None.
        """
        if not self._provider:
            return

        # Build a new profile with default values and attach it to the provider.
        new_profile = LaunchProfileModel.get_default(name)
        self._provider.launch_profiles.append(new_profile)
        self._service_provider.update_provider(self._provider)

        self._refresh_profiles_list()
        self._view.set_selected_profile(new_profile.id_profile)
        self._on_profile_selected(new_profile.id_profile)

    def _on_profile_delete(self, id_profile: str) -> None:
        """Remove a profile from the provider and persist the change.

        Args:
            id_profile: Unique identifier of the profile to delete.
        """
        if not self._provider:
            return

        # Remove the matching profile from the list.
        self._provider.launch_profiles = [p for p in self._provider.launch_profiles if p.id_profile != id_profile]
        self._service_provider.update_provider(self._provider)
        self._refresh_profiles_list()

        # No profile is selected after deletion — disable rename/save, keep file date.
        self._view.set_rename_profile_button_state(False)
        self._view.set_save_profile_button_state(False)
        self._view.set_profile_modified_date(self._provider.modified_date_provider)

    def _on_profile_rename(self, id_profile: str, new_name: str) -> None:
        """Rename the given profile, persist the change, and refresh the list.

        Args:
            id_profile: Unique identifier of the profile to rename.
            new_name: Name entered by the user.

        Returns:
            None.
        """
        profile = self._find_profile(id_profile)
        if profile is None:
            return

        # Apply the new name and stamp the modification date.
        profile.name_profile = new_name
        profile.mark_profile_as_modified()
        self._service_provider.update_provider(self._provider)

        # Restore selection and update the date label with the provider file date.
        self._refresh_profiles_list()
        self._view.set_selected_profile(id_profile)
        self._view.set_rename_profile_button_state(True)
        self._view.set_save_profile_button_state(True)
        self._view.set_profile_modified_date(self._provider.modified_date_provider)

    def _on_profile_save(self, id_profile: str) -> None:
        """Persist current form settings into the profile without changing its name.

        Args:
            id_profile: Unique identifier of the profile to save.

        Returns:
            None.
        """
        profile = self._find_profile(id_profile)
        if profile is None:
            return

        profile.export_folder = self._view.get_export_folder() or profile.export_folder

        url_source = self._view.get_url_source()
        profile.url_source_type = url_source.get("type", profile.url_source_type)
        raw_value = url_source.get("value")
        if raw_value is not None:
            profile.url_source_value = raw_value

        threshold = self._view.get_emergency_stop_threshold()
        if threshold is not None:
            profile.emergency_stop_threshold = threshold

        profile.mark_profile_as_modified()
        self._service_provider.update_provider(self._provider)
        self._is_profile_dirty = False

        self._refresh_profiles_list()
        self._view.set_selected_profile(id_profile)
        self._view.set_save_profile_button_state(True)
        self._view.set_rename_profile_button_state(True)
        self._view.set_profile_modified_date(self._provider.modified_date_provider)

    def _find_profile(self, id_profile: str | None) -> LaunchProfileModel | None:
        """Search the current provider's profiles for a matching id_profile.

        Args:
            id_profile: The profile identifier to look for.

        Returns:
            LaunchProfileModel | None: The matching profile, or None if not found.
        """
        if not self._provider or not id_profile:
            return None

        for profile in self._provider.launch_profiles:
            if profile.id_profile == id_profile:
                return profile
        return None

    def _refresh_profiles_list(self) -> None:
        """Rebuild the profile Listbox in the view from the current provider.

        Returns:
            None.
        """
        if not self._provider:
            self._view.render_profiles_list([])
            return

        rows = [{"id_profile": p.id_profile, "name_profile": p.name_profile} for p in self._provider.launch_profiles]
        self._view.render_profiles_list(rows)

    def _on_form_changed(self) -> None:
        """React to user-driven changes in the launch-profile form.

        Sets the dirty flag and enables the save button only when a profile
        is selected (otherwise the save button stays disabled).

        Returns:
            None.
        """
        self._is_profile_dirty = True

    def _on_manual_urls_confirmed(self, raw: str) -> None:
        """Parse raw URL text from the view and update the active URL source.

        Args:
            raw: Multiline string typed by the user — one URL per line.
        """
        urls = [line.strip() for line in raw.splitlines() if line.strip()]
        self._view.set_url_source("manual", urls)
        self._on_form_changed()

    def _on_open_export_folder(self) -> None:
        """Create the export folder if absent, then reveal it in the file explorer."""
        folder = self._view.get_export_folder()
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        open_folder(path)

    def _load_last_used_profile(self) -> None:
        """Select and apply the most recently launched profile in the view.

        Returns:
            None.
        """
        if not self._provider or not self._provider.launch_profiles:
            self._view.set_launch_profile_enabled(False)
            return

        # Select the profile with the most recent used_date_profile if any.
        used = [p for p in self._provider.launch_profiles if p.used_date_profile]
        target = max(used, key=lambda p: p.used_date_profile or "") if used else self._provider.launch_profiles[0]

        self._view.set_selected_profile(target.id_profile)
        self._on_profile_selected(target.id_profile)

    def _record_active_profile_launch(self) -> None:
        """Snapshot view inputs into the active profile and increment its launch counter.

        The caller is responsible for persisting the provider after this call.

        Returns:
            None.
        """
        id_profile = self._view.get_selected_id_profile()
        profile = self._find_profile(id_profile)
        if profile is None:
            return

        profile.export_folder = self._view.get_export_folder() or profile.export_folder

        url_source = self._view.get_url_source()
        profile.url_source_type = url_source.get("type", profile.url_source_type)
        raw_value = url_source.get("value")
        if raw_value is not None:
            profile.url_source_value = raw_value

        # Persist validated threshold; keep existing value when the field is invalid.
        threshold = self._view.get_emergency_stop_threshold()
        if threshold is not None:
            profile.emergency_stop_threshold = threshold

        profile.increment_launch_count()

    def _persist_provider_before_launch(self) -> None:
        """Save the in-memory provider to disk before starting the workflow.

        Returns:
            None.
        """
        if self._provider:
            self._service_provider.update_provider(self._provider)

    # ------------------------------------------------------------------
    # Workflow control callbacks
    # ------------------------------------------------------------------

    def _check_launch_preconditions(self) -> bool:
        """Return True if all launch guards pass; show a warning and return False if any fails."""
        # Provider must be loaded before launching.
        if not self._provider:
            self._view.show_warning(C_SCRAPING_NO_PROVIDER_LOADED)
            return False

        # Block launch when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._view.show_warning(C_SCRAPING_WORKFLOW_ACTIVE_LAUNCH)
            return False

        # Confirm intent when no URL source is configured.
        url_source = self._view.get_url_source()
        if not url_source.get("type") and not self._view.ask_confirm_launch_without_source():
            return False

        # Abort when the emergency stop threshold is invalid.
        if self._view.get_emergency_stop_threshold() is None:
            self._view.show_warning(C_SCRAPING_EMERGENCY_STOP_INVALID_MSG)
            return False

        return True

    def _on_launch(self) -> None:
        """Start the workflow in a daemon background thread.

        Returns:
            None.
        """
        if not self._check_launch_preconditions():
            return

        # Reset signals and journal counter from any previous run.
        self._pause_event.set()
        self._cancel_event.clear()
        self._all_logs_scraping = []
        self._view.set_running_state(True)

        self._record_active_profile_launch()
        self._persist_provider_before_launch()

        # Refresh the date label — update_provider stamped a new modified_date.
        self._view.set_profile_modified_date(self._provider.modified_date_provider)
        self._start_workflow_thread()

    def _start_workflow_thread(self) -> None:
        """Collect view inputs and spawn the workflow daemon thread.

        Returns:
            None.
        """
        started_at = datetime.now()
        self._view.start_elapsed_timer(started_at)

        export_folder = self._view.get_export_folder()
        self._emergency_stop_threshold = self._view.get_emergency_stop_threshold() or 0
        url_source = self._view.get_url_source()
        source_type: str = url_source["type"]
        raw_value = url_source["value"]
        source_value: list[str] | str = raw_value if raw_value is not None else []

        self._thread = threading.Thread(
            target=self._run_workflow,
            args=(source_type, source_value, export_folder),
            daemon=True,
        )
        self._thread.start()

    def _on_cancel(self) -> None:
        """Signal the running workflow to abort after the current step.

        Returns:
            None.
        """
        # Unblock any pause so the cancel signal is observed immediately.
        asked_agree = self._view.ask_confirm_cancel_browsing()
        if asked_agree:
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

    def _on_emergency_stop(self) -> None:
        """Called by the service when the failure quota exceeds the threshold.

        Transitions the view to the paused state from the background thread so
        the user can review errors and choose to resume or cancel.
        """
        # Called from the background thread; set_paused_state is thread-safe.
        self._view.set_paused_state(True)

    # ------------------------------------------------------------------
    # Step lifecycle callbacks
    # ------------------------------------------------------------------

    def _on_logging_event(
        self, event: EventScrapingEnum, step: StepScrapingModel, context: ScrapingContextModel
    ) -> None:
        """Route a scraping lifecycle event to the matching journal handler.

        Args:
            event: The lifecycle event emitted by the scraping service.
            step: The step model associated with the event.
            context: The current scraping context.
        """
        if event == EventScrapingEnum.E_STEP_START:
            self._on_logging_event_start(step, context)
        elif event == EventScrapingEnum.E_STEP_DONE:
            self._on_logging_event_done(step, context)
        elif event == EventScrapingEnum.E_EMERGENCY_STOP:
            self._on_logging_event_stop(step, context)
        elif event == EventScrapingEnum.E_BROWSER_INIT:
            self._on_logging_event_msg(C_SCRAPING_EVENT_BROWSER_INIT)
        elif event == EventScrapingEnum.E_CONTEXT_INIT:
            self._on_logging_event_msg(C_SCRAPING_EVENT_CONTEXT_INIT)
        elif event == EventScrapingEnum.E_WORKFLOW_INIT:
            self._on_logging_event_msg(C_SCRAPING_EVENT_WORKFLOW_INIT)

    def _on_logging_event_start(self, step: StepScrapingModel, context: ScrapingContextModel) -> None:
        """Called by the service just before a step executes.

        Inserts a pending row in the journal so the user sees the step
        name immediately, before the result is known.

        Args:
            step: The step model about to execute.
            context: The current scraping context, containing live stats and info.
        """
        str_suffix = ""
        if (
            step.step_type == StepTypeEnum.E_OPEN_URL
            and step.params[C_KEY_URL_MODE] == OpenUrlModeEnum.E_SOURCE.value
            and context.url_source
        ):
            str_suffix = " | " + context.url_source.display_progress_tuple_text()

        if step.step_type == StepTypeEnum.E_EXTRACT_TEXT:
            str_suffix = (
                " | Mode"
                + step.params.get("extract_mode", "")
                + " | Cible: "
                + step.params.get("target", "")
                + " | Sélecteur: "
                + step.params.get("selector", "")
            )

        # Build the journal entry with the optional source progress suffix.
        str_entry = f"{get_time_now_hh_mm_ss()} | Début '{step.step_type.value}'{str_suffix}\n"

        # logs
        self._all_logs_scraping.append(str_entry)
        self._view.add_journal_entry(str_entry)

    def _on_logging_event_stop(self, step: StepScrapingModel, context: ScrapingContextModel) -> None:
        """Called by the service when workflow stopped.

        Args:
            step: The step model about to execute.
            context: The current scraping context, containing live stats and info.
        """
        str_entry = f"{get_time_now_hh_mm_ss()} | Emergency stop threshold reached\n"

        # logs
        self._all_logs_scraping.append(str_entry)
        self._view.add_journal_entry(str_entry)

        # Push live progress values to the progression frame.
        self._view.update_progress(
            url=context.last_url_opened,
            status=C_SCRAPING_STATUS_EMERGENCY_STOP,
            stats_text=self._service_scraping.current_stats,
        )

    def _on_logging_event_done(self, step: StepScrapingModel, context: ScrapingContextModel) -> None:
        """Called by the service after each step completes.

        Updates the pre-inserted journal row and refreshes the progress frame.

        Args:
            step: The completed step model.
            context: The current scraping context, containing live stats and info.
        """
        # Complete the journal row started in _on_step_start.
        date_str = get_time_now_hh_mm_ss()
        is_success = C_SCRAPING_JOURNAL_RESULT_OK if context.last_result_step else C_SCRAPING_JOURNAL_RESULT_ERROR
        line = (
            f"{date_str} | {step.step_type.value} | {is_success}"
            f" | {context.last_time_elapsed:.3f} | {context.last_message_step}\n"
        )

        # logs
        self._all_logs_scraping.append(line)
        self._view.add_journal_entry(str_entry=line)

        # Push live progress values to the progression frame.
        self._view.update_progress(
            url=context.last_url_opened,
            status=C_SCRAPING_JOURNAL_PENDING_STATUS,
            stats_text=self._service_scraping.current_stats,
        )

    def _on_logging_event_msg(self, message: str) -> None:
        """Append a free-form message to the journal and update the progress frame.

        Args:
            message: Text to display as the current status and append to the journal.
        """
        # Build the timestamped journal line.
        date_str = get_time_now_hh_mm_ss()
        line = f"{date_str} | {message}\n"

        # logs
        self._all_logs_scraping.append(line)
        self._view.add_journal_entry(str_entry=line)

        # Push live progress values to the progression frame.
        self._view.update_progress(
            url="",
            status=message,
            stats_text=self._service_scraping.current_stats,
        )

    def _on_logging_event_final_report(self, r: ScrapingReportModel) -> None:
        """Append the run summary line to the journal.

        Args:
            r: The completed scraping report containing all counters.
        """
        # Build the summary line from all report counters.
        date_str = get_time_now_hh_mm_ss()
        line = f"{date_str} | Début {r.started_at} | Fin {r.finished_at}"
        line += f" | Total steps x{r.steps_total} | Succès x{r.steps_success} | Erreur x{r.steps_failed}"
        line += f" | Clique x{r.clicks_performed} | URL ouverte x{r.open_urls_executed} | Est annulé = {r.cancelled}\n"

        # logs
        self._all_logs_scraping.append(line)
        self._view.add_journal_entry(str_entry=line)

    # ------------------------------------------------------------------
    # Workflow thread target
    # ------------------------------------------------------------------

    def _call_service_workflow(
        self, url_source_type: str, url_source_value: list[str] | str, export_folder: str
    ) -> ScrapingReportModel | None:
        """Invoke the scraping service; return the report or None on exception.

        Args:
            url_source_type: URL source type string (``"manual"``, ``"csv"``,
                ``"folder"``, or ``""`` when no source is configured).
            url_source_value: Matching value — list of URLs or path string.
            export_folder: Path to the folder where results should be exported.

        Returns:
            The completed ScrapingReportModel, or None if an exception was raised.
        """
        try:
            return self._service_scraping.run_workflow(
                self._provider,
                url_source_type,
                url_source_value,
                export_folder,
                self._cancel_event,
                self._pause_event,
                self._on_user_wait_step,
                self._on_logging_event,
                self._emergency_stop_threshold,
                self._on_emergency_stop,
            )
        except ValueError, RuntimeError, OSError:
            self._logging.exception("Échec de l'exécution du workflow")
            return None

    def _run_workflow(self, url_source_type: str, url_source_value: list[str] | str, export_folder: str) -> None:
        """Thread target: run the workflow and dispatch the result to the view.

        Args:
            url_source_type: URL source type string passed to the service.
            url_source_value: Matching value — list of URLs or path string.
            export_folder: Path to the folder where results should be exported.
        """
        report = self._call_service_workflow(url_source_type, url_source_value, export_folder)
        self._on_workflow_finished(report, export_folder)

    def _push_final_status(self, report: ScrapingReportModel | None) -> None:
        """Push the completed-run status and statistics to the progress frame.

        Args:
            report: Completed report, or None when the run raised an exception.
        """
        if report is not None:
            status = C_SCRAPING_STATUS_CANCELLED if report.cancelled else C_SCRAPING_STATUS_FINISHED
            self._view.update_progress(url="", status=status, stats_text=report)
        else:
            self._view.update_progress(url="", status=C_SCRAPING_STATUS_ERROR, stats_text=None)

    def _on_workflow_finished(self, report: ScrapingReportModel | None, export_folder: str) -> None:
        """Restore idle state and display the final report in the view.

        Args:
            report: Completed report, or None when the run raised an exception.
            export_folder: Destination folder used for auto-export when enabled.
        """
        # Ensure pause is released so the event is ready for the next run.
        self._pause_event.set()
        self._view.set_running_state(False)
        self._push_final_status(report)

        # Schedule auto-export on the main thread (Treeview access is not thread-safe).
        if report:
            self._on_logging_event_final_report(report)
        self._view.after(0, lambda: self._do_auto_export(export_folder))

    def _do_auto_export(self, export_folder: str) -> None:
        """Export the scraping journal automatically with a timestamped filename.

        Must be called from the main thread — accesses Treeview rows via the view.

        Args:
            export_folder: Destination folder for the exported file.
        """
        timestamp = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        path = str(Path(export_folder) / f"journal_{timestamp}.txt")
        self._on_export_journal(path)
