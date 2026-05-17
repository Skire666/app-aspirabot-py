"""Scraping panel — thin orchestrator composing five sub-panels.

ScrapingView wires the five sub-panels together and exposes the same public
interface that ScrapingPresenter expects. No widget logic lives here; all
behaviour is delegated to the appropriate panel.

Example:
    >>> panel = ScrapingView(config_model, content_area)
    >>> panel.set_on_launch(lambda: print("launch"))
    >>> panel.reset()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from shared.i18n_fra import C_SCRAPING_NO_URL_SOURCE_MSG, C_SCRAPING_NO_URL_SOURCE_TITLE
from views.scraping.launch_profile_panel import LaunchProfilePanel
from views.scraping.profile_management_panel import ProfileManagementPanel
from views.scraping.provider_selection_panel import ProviderSelectionPanel
from views.scraping.scraping_journal_panel import ScrapingJournalPanel
from views.scraping.workflow_controls_panel import WorkflowControlsPanel

from __src__.models.scraping_report_model import ScrapingReportModel

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ScrapingView(ttk.Frame):  # pylint: disable=too-many-public-methods
    """Scraping panel composed of five vertically stacked sub-panels.

    Panel order (top to bottom):
    1. ProviderSelectionPanel  — provider combobox.
    2. ProfileManagementPanel  — profile listbox and CRUD buttons.
    3. LaunchProfilePanel      — export folder, URL source, auto-export.
    4. WorkflowControlsPanel   — progress rows and control buttons.
    5. ScrapingJournalPanel    — step-by-step Treeview journal.
    """

    def __init__(self, config_model: AppConfigurationModel, parent: tk.Widget) -> None:
        """Initialize the scraping panel by composing five sub-panels.

        Args:
            config_model: Application configuration providing the default export folder.
            parent: The parent Tkinter widget (e.g. main_view.content_area).
        """
        super().__init__(parent)
        self._create_panels(config_model)

    def _create_panels(self, config_model: AppConfigurationModel) -> None:
        """Instantiate and pack the five sub-panels in display order.

        Args:
            config_model: Application configuration forwarded to LaunchProfilePanel.
        """
        self._provider_panel: ProviderSelectionPanel = ProviderSelectionPanel(self)
        self._provider_panel.pack(side=tk.TOP, fill=tk.X)

        self._profile_panel: ProfileManagementPanel = ProfileManagementPanel(self)
        self._profile_panel.pack(side=tk.TOP, fill=tk.X)

        self._launch_panel: LaunchProfilePanel = LaunchProfilePanel(config_model, self)
        self._launch_panel.pack(side=tk.TOP, fill=tk.X)

        self._workflow_panel: WorkflowControlsPanel = WorkflowControlsPanel(self)
        self._workflow_panel.pack(side=tk.TOP, fill=tk.X)

        self._journal_panel: ScrapingJournalPanel = ScrapingJournalPanel(self)
        self._journal_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # ---------------------------------------------------------------
    # Workflow callbacks and state — delegates to WorkflowControlsPanel
    # ---------------------------------------------------------------

    def set_on_launch(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Lancer.

        Args:
            callback: Zero-argument callable that starts the workflow.
        """
        self._workflow_panel.set_on_launch(callback)

    def set_on_cancel(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Annuler.

        Args:
            callback: Zero-argument callable that signals cancellation.
        """
        self._workflow_panel.set_on_cancel(callback)

    def set_on_pause(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Pause.

        Args:
            callback: Zero-argument callable that pauses the workflow.
        """
        self._workflow_panel.set_on_pause(callback)

    def set_on_resume(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Reprendre.

        Args:
            callback: Zero-argument callable that resumes the workflow.
        """
        self._workflow_panel.set_on_resume(callback)

    def set_running_state(self, running: bool) -> None:
        """Toggle button states to match whether a workflow is in progress.

        Safe to call from a background thread.

        Args:
            running: True while the workflow is running; False when idle.
        """
        self._workflow_panel.set_running_state(running)

    def set_paused_state(self, paused: bool) -> None:
        """Toggle Pause/Reprendre buttons to match the paused state.

        Safe to call from a background thread.

        Args:
            paused: True while the workflow is paused; False when running.
        """
        self._workflow_panel.set_paused_state(paused)

    def update_progress(
        self,
        url: str,
        tabs: int,
        current_step: str,
        status: str,
        stats_text: ScrapingReportModel | None,
    ) -> None:
        """Push live progress values to the progression panel.

        Safe to call from a background thread.

        Args:
            url: Current browser page URL.
            tabs: Number of open browser tabs.
            current_step: Label of the step currently executing.
            status: Workflow status label.
            stats_text: Pre-formatted statistics string built by the presenter.
        """
        self._workflow_panel.update_progress(url, tabs, current_step, status, stats_text)

    def start_elapsed_timer(self, started_at: datetime) -> None:
        """Start the elapsed-time ticker in the progression panel.

        Safe to call from a background thread.

        Args:
            started_at: The datetime at which the workflow started.
        """
        self._workflow_panel.start_elapsed_timer(started_at)

    # ---------------------------------------------------------------
    # Provider callbacks and data — delegates to ProviderSelectionPanel
    # ---------------------------------------------------------------

    def set_on_provider_selected(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user selects a provider.

        Args:
            callback: Callable receiving the selected provider's id_file.
        """
        self._provider_panel.set_on_provider_selected(callback)

    def set_on_refresh_providers(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Rafraîchir.

        Args:
            callback: Zero-argument callable that reloads the provider list.
        """
        self._provider_panel.set_on_refresh_providers(callback)

    def render_providers_list(self, providers: list[dict[str, Any]]) -> None:
        """Populate the provider combobox and lock dependent panels if needed.

        When the previously selected provider is absent from the refreshed list,
        the profile panel and the launch button are disabled.

        Args:
            providers: List of dicts with keys ``id_file``, ``provider_name``,
                ``url``, ``version``, ``modified_date``.
        """
        selection_retained = self._provider_panel.render_providers_list(providers)
        if not selection_retained:
            self._profile_panel.set_enabled(False)
            self._workflow_panel.set_launch_enabled(False)

    def set_selected_provider(self, id_file: str) -> None:
        """Highlight the combobox entry matching id_file.

        Args:
            id_file: The unique provider file identifier to select.
        """
        self._provider_panel.set_selected_provider(id_file)

    # ---------------------------------------------------------------
    # Profile callbacks and data — delegates to ProfileManagementPanel
    # ---------------------------------------------------------------

    def set_on_profile_selected(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user selects a profile.

        Args:
            callback: Callable receiving the selected profile_id.
        """
        self._profile_panel.set_on_profile_selected(callback)

    def set_on_profile_new(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user confirms a new profile name.

        Args:
            callback: Callable receiving the profile name entered by the user.
        """
        self._profile_panel.set_on_profile_new(callback)

    def set_on_profile_delete(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user deletes a profile.

        Args:
            callback: Callable receiving the profile_id to remove.
        """
        self._profile_panel.set_on_profile_delete(callback)

    def set_on_profile_rename(self, callback: Callable[[str, str], None]) -> None:
        """Register the callback fired when the user renames a profile.

        Args:
            callback: Callable receiving (profile_id, new_name).
        """
        self._profile_panel.set_on_profile_rename(callback)

    def render_profiles_list(self, profiles: list[dict[str, Any]]) -> None:
        """Populate the profile Listbox and disable the launch form when empty.

        Args:
            profiles: List of dicts with keys ``profile_id`` and ``name``.
        """
        self._profile_panel.render_profiles_list(profiles)
        if not profiles:
            self._launch_panel.set_enabled(False)
            self._profile_panel.set_rename_profile_button_state(False)

    def get_selected_profile_id(self) -> str | None:
        """Return the profile_id of the highlighted Listbox entry.

        Returns:
            str | None: The profile_id of the selected entry, or None.
        """
        return self._profile_panel.get_selected_profile_id()

    def set_selected_profile(self, profile_id: str) -> None:
        """Highlight the Listbox entry matching profile_id.

        Args:
            profile_id: The profile identifier to select.
        """
        self._profile_panel.set_selected_profile(profile_id)

    def set_profile_management_enabled(self, enabled: bool) -> None:
        """Enable or disable all widgets inside the profile management panel.

        Args:
            enabled: True to make the panel interactive; False to gray it out.
        """
        self._profile_panel.set_enabled(enabled)

    def set_rename_profile_button_state(self, enabled: bool) -> None:
        """Enable or disable the 'Renommer profil' button.

        Args:
            enabled: True when a profile is selected.
        """
        self._profile_panel.set_rename_profile_button_state(enabled)

    def set_profile_modified_date(self, date_str: str | None) -> None:
        """Update the last-modification date label in the profile panel.

        Args:
            date_str: ISO datetime string, or None to show a placeholder.
        """
        self._profile_panel.set_profile_modified_date(date_str)

    # ---------------------------------------------------------------
    # Launch-form callbacks, setters, getters — delegates to LaunchProfilePanel
    # ---------------------------------------------------------------

    def set_on_form_changed(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user modifies the launch profile form.

        Args:
            callback: Zero-argument callable notified on every user-driven change.
        """
        self._launch_panel.set_on_form_changed(callback)

    def set_on_manual_urls_confirmed(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user confirms manual URLs.

        Args:
            callback: Callable receiving the raw multiline text entered by the user.
        """
        self._launch_panel.set_on_manual_urls_confirmed(callback)

    def set_on_open_export_folder(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks 'Ouvrir dossier'.

        Args:
            callback: Zero-argument callable that creates the folder and opens it.
        """
        self._launch_panel.set_on_open_export_folder(callback)

    def set_export_folder(self, folder: str) -> None:
        """Set the export folder entry and internal state.

        Args:
            folder: Absolute path to apply to the export folder field.
        """
        self._launch_panel.set_export_folder(folder)

    def set_url_source(self, source_type: str, source_value: list[str] | str | None) -> None:
        """Restore the URL source radio selection and internal value.

        Args:
            source_type: One of ``"manual"``, ``"folder"``, ``"csv"``, or ``""``.
            source_value: Matching value — list of URLs, a path string, or None.
        """
        self._launch_panel.set_url_source(source_type, source_value)

    def set_launch_profile_enabled(self, enabled: bool) -> None:
        """Enable or disable all widgets inside the launch profile panel.

        Args:
            enabled: True to make the panel interactive; False to gray it out.
        """
        self._launch_panel.set_enabled(enabled)

    def get_export_folder(self) -> str:
        """Return the currently selected export folder path.

        Returns:
            str: Absolute path of the selected export folder.
        """
        return self._launch_panel.get_export_folder()

    def get_url_source(self) -> dict[str, Any]:
        """Return the selected URL source type and its collected value.

        Returns:
            Dict with keys ``type`` and ``value``.
        """
        return self._launch_panel.get_url_source()

    def get_auto_export_journal(self) -> bool:
        """Return whether the auto-export journal checkbox is checked.

        Returns:
            bool: True when the journal should be exported automatically.
        """
        return self._launch_panel.get_auto_export_journal()

    def get_emergency_stop_threshold(self) -> int | None:
        """Return the emergency stop threshold from the launch profile panel.

        Returns:
            int | None: A valid threshold between 1 and 9999999, or None if invalid.
        """
        return self._launch_panel.get_emergency_stop_threshold()

    def set_emergency_stop_threshold(self, value: int) -> None:
        """Set the emergency stop threshold in the launch profile panel.

        Args:
            value: Threshold to display (must be between 1 and 9999999).
        """
        self._launch_panel.set_emergency_stop_threshold(value)

    # ---------------------------------------------------------------
    # Journal callbacks and entries — delegates to ScrapingJournalPanel
    # ---------------------------------------------------------------

    def set_on_export_journal(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when a journal export is requested.

        Args:
            callback: Callable receiving the chosen destination file path.
        """
        self._journal_panel.set_on_export_journal(callback)

    def start_journal_entry(self, item_id: str, date: str, step_started: str) -> None:
        """Insert a pending journal row before the step executes.

        Safe to call from a background thread.

        Args:
            item_id: Unique Treeview iid used to update the row later.
            date: Timestamp string captured at step start.
            step_started: Step type label (e.g. ``"OPEN_URL"``).
        """
        self._journal_panel.start_journal_entry(item_id, date, step_started)

    def complete_journal_entry(
        self,
        item_id: str,
        msg_step_ended: str,
        success: bool,
        duration_s: float,
    ) -> None:
        """Update the pending journal row once the step has finished.

        Safe to call from a background thread.

        Args:
            item_id: The iid returned by ``start_journal_entry``.
            msg_step_ended: Result message from the executor.
            success: True for a successful step; False for an error.
            duration_s: Wall-clock duration of the step in seconds.
        """
        self._journal_panel.complete_journal_entry(item_id, msg_step_ended, success, duration_s)

    def get_journal_rows(self) -> list[tuple[str, ...]]:
        """Return the current journal rows as a list of value tuples.

        Returns:
            Ordered list of row tuples (date, step_started, duration, result, message).
        """
        return self._journal_panel.get_journal_rows()

    # ---------------------------------------------------------------
    # Panel-level operations
    # ---------------------------------------------------------------

    def reset(self) -> None:
        """Reset run-specific UI elements to their initial idle state.

        Clears the progression fields and the journal Treeview. Restores
        all buttons to idle. Must be called from the main thread.
        """
        self._workflow_panel.reset()
        self._journal_panel.clear()

    @staticmethod
    def ask_confirm_launch_without_source() -> bool:
        """Show a confirmation dialog when no URL source has been selected.

        Returns:
            True when the user accepts to continue despite the missing source.
        """
        return messagebox.askokcancel(
            C_SCRAPING_NO_URL_SOURCE_TITLE,
            C_SCRAPING_NO_URL_SOURCE_MSG,
        )

    @staticmethod
    def ask_confirm_cancel_browsing() -> bool:
        """Show a confirmation dialog when the user tries to cancel while browsing.

        Returns:
            True when the user confirms they want to cancel immediately.
        """
        return messagebox.askokcancel(
            "Confirmer l'annulation",
            "Le processus de navigation est en cours. Confirmez-vous que vous voulez annuler immédiatement ?",
        )

    @staticmethod
    def show_warning(message: str) -> None:
        """Display a warning message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showwarning("Avertissement", message)


# EOF
