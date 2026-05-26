"""Scraping panel — thin orchestrator composing five sub-panels.

ScrapingView wires the five sub-panels together and exposes the same public
interface that ScrapingPresenter expects. No widget logic lives here; all
behaviour is delegated to the appropriate panel.

Example:
    >>> panel = ScrapingView(config_model, content_area)
    >>> panel.bind_callbacks(ScrapingViewCallbacks(on_launch=..., ...))
    >>> panel.reset()
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from models.scraping_report_model import ScrapingReportModel
from shared.i18n_fra import C_SCRAPING_NO_URL_SOURCE_MSG, C_SCRAPING_NO_URL_SOURCE_TITLE
from views.scraping.launch_profile_panel import LaunchProfilePanel
from views.scraping.profile_management_panel import ProfileManagementPanel
from views.scraping.provider_selection_panel import ProviderSelectionPanel
from views.scraping.scraping_journal_panel import ScrapingJournalPanel
from views.scraping.workflow_controls_panel import WorkflowControlsPanel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ScrapingViewCallbacks:
    """All callbacks the presenter wires onto ScrapingView in one call."""

    on_launch: Callable[[], None]
    on_cancel: Callable[[], None]
    on_pause: Callable[[], None]
    on_resume: Callable[[], None]
    on_provider_selected: Callable[[str], None]
    on_refresh_scenarios: Callable[[], None]
    on_profile_selected: Callable[[str], None]
    on_profile_new: Callable[[str], None]
    on_profile_delete: Callable[[str], None]
    on_profile_rename: Callable[[str, str], None]
    on_profile_save: Callable[[str], None]
    on_form_changed: Callable[[], None]
    on_manual_urls_confirmed: Callable[[str], None]
    on_open_export_folder: Callable[[], None]
    on_export_journal: Callable[[str], None]


class ScrapingView(ttk.Frame):
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
    # Callback wiring
    # ---------------------------------------------------------------

    def bind_callbacks(self, callbacks: ScrapingViewCallbacks) -> None:
        """Register all presenter handlers on this view in a single call."""
        self._workflow_panel.set_on_launch(callbacks.on_launch)
        self._workflow_panel.set_on_cancel(callbacks.on_cancel)
        self._workflow_panel.set_on_pause(callbacks.on_pause)
        self._workflow_panel.set_on_resume(callbacks.on_resume)
        self._provider_panel.set_on_provider_selected(callbacks.on_provider_selected)
        self._provider_panel.set_on_refresh_scenarios(callbacks.on_refresh_scenarios)
        self._profile_panel.set_on_profile_selected(callbacks.on_profile_selected)
        self._profile_panel.set_on_profile_new(callbacks.on_profile_new)
        self._profile_panel.set_on_profile_delete(callbacks.on_profile_delete)
        self._profile_panel.set_on_profile_rename(callbacks.on_profile_rename)
        self._profile_panel.set_on_profile_save(callbacks.on_profile_save)
        self._launch_panel.set_on_form_changed(callbacks.on_form_changed)
        self._launch_panel.set_on_manual_urls_confirmed(callbacks.on_manual_urls_confirmed)
        self._launch_panel.set_on_open_export_folder(callbacks.on_open_export_folder)
        self._journal_panel.set_on_export_journal(callbacks.on_export_journal)

    # ---------------------------------------------------------------
    # Workflow state — delegates to WorkflowControlsPanel
    # ---------------------------------------------------------------

    def set_running_state(self, running: bool) -> None:
        """Toggle button states to match whether a workflow is in progress.

        Safe to call from a background thread.

        Args:
            running: True while the workflow is running; False when idle.
        """
        if running:
            # true, but we want to reset the journal when starting a new run
            self._journal_panel.clear()
        self._set_top_panels_enabled(not running)
        self._workflow_panel.set_running_state(running)

    def _set_top_panels_enabled(self, enabled: bool) -> None:
        """Enable or disable the three configuration panels above the workflow area."""
        self._provider_panel.set_enabled(enabled)
        self._profile_panel.set_enabled(enabled)
        self._launch_panel.set_enabled(enabled)

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
        status: str,
        stats_text: ScrapingReportModel | None,
    ) -> None:
        """Push live progress values to the progression panel.

        Safe to call from a background thread.

        Args:
            url: Current browser page URL.
            status: Workflow status label.
            stats_text: Pre-formatted statistics string built by the presenter.
        """
        self._workflow_panel.update_progress(url, status, stats_text)

    def start_elapsed_timer(self, started_at: datetime) -> None:
        """Start the elapsed-time ticker in the progression panel.

        Safe to call from a background thread.

        Args:
            started_at: The datetime at which the workflow started.
        """
        self._workflow_panel.start_elapsed_timer(started_at)

    # ---------------------------------------------------------------
    # Provider data — delegates to ProviderSelectionPanel
    # ---------------------------------------------------------------

    def render_providers_list(self, providers: list[dict[str, Any]]) -> None:
        """Populate the provider combobox and lock dependent panels if needed.

        When the previously selected provider is absent from the refreshed list,
        the profile panel and the launch button are disabled.

        Args:
            providers: List of dicts with keys ``id_file``, ``provider_name``,
                ``provider_desc``, ``version``, ``modified_date``.
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
    # Profile data — delegates to ProfileManagementPanel
    # ---------------------------------------------------------------

    def render_profiles_list(self, profiles: list[dict[str, Any]]) -> None:
        """Populate the profile Listbox and disable the launch form when empty.

        Args:
            profiles: List of dicts with keys ``id_profile`` and ``name_profile``.
        """
        self._profile_panel.render_profiles_list(profiles)
        if not profiles:
            self._launch_panel.set_enabled(False)
            self._profile_panel.set_rename_profile_button_state(False)
            self._profile_panel.set_save_profile_button_state(False)

    def get_selected_id_profile(self) -> str | None:
        """Return the id_profile of the highlighted Listbox entry.

        Returns:
            str | None: The id_profile of the selected entry, or None.
        """
        return self._profile_panel.get_selected_id_profile()

    def set_selected_profile(self, id_profile: str) -> None:
        """Highlight the Listbox entry matching id_profile.

        Args:
            id_profile: The profile identifier to select.
        """
        self._profile_panel.set_selected_profile(id_profile)

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

    def set_save_profile_button_state(self, enabled: bool) -> None:
        """Enable or disable the 'Sauvegarder' button.

        Args:
            enabled: True when a profile is selected.
        """
        self._profile_panel.set_save_profile_button_state(enabled)

    def set_profile_modified_date(self, dt: datetime | None) -> None:
        """Update the last-modification date label in the profile panel.

        Args:
            dt: Datetime object representing the modification date, or None to show a placeholder.
        """
        self._profile_panel.set_profile_modified_date(dt)

    # ---------------------------------------------------------------
    # Launch-form setters and getters — delegates to LaunchProfilePanel
    # ---------------------------------------------------------------

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
    # Journal entries — delegates to ScrapingJournalPanel
    # ---------------------------------------------------------------

    def add_journal_entry(self, str_entry: str) -> None:
        """Insert a pending journal row before the step executes.

        Safe to call from a background thread.

        Args:
            str_entry: The journal entry string to add.
        """
        self._journal_panel.add_journal_entry(str_entry)

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
