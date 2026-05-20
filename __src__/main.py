"""Application entry point for Aspirabot."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import models.steps  # noqa: F401
import services.steps  # noqa: F401
import views.steps  # noqa: F401
from models.app_configuration_model import AppConfigurationModel
from presenters.app_configuration_presenter import AppConfigurationPresenter
from presenters.debug_presenter import DebugPresenter
from presenters.historic_presenter import HistoricPresenter
from presenters.log_presenter import LogPresenter
from presenters.provider_presenter import ProviderPresenter
from presenters.scraping_presenter import ScrapingPresenter
from presenters.splashscreen_presenter import SplashscreenPresenter
from presenters.workflow_presenter import WorkflowPresenter
from repositories.app_configuration_repository import AppConfigurationRepository
from repositories.log_repository import LogRepository
from repositories.providers_repository import ProvidersRepository
from repositories.scraping_journal_repository import ScrapingJournalRepository
from services.app_configuration_service import ConfigService
from services.historic_service import HistoricService
from services.logging_service import LoggingService
from services.provider_service import ProviderService
from services.scraping_service import ScrapingService
from services.startup_service import StartupService

# Bootstrap: import all step packages to populate the central registry.
from services.workflow_service import WorkflowService
from shared.constants import (
    C_APP_CONFIG_FILE,
)
from shared.i18n_fra import TitleModuleEnum
from shared.path_util import get_current_working_directory
from views.app_configuration_view import AppConfigurationView
from views.debug_view import DebugView
from views.faq_view import FaqView
from views.historic_view import HistoricView
from views.log_view import LogView
from views.main_view import MainView
from views.providers_view import ProvidersView
from views.scraping_view import ScrapingView
from views.splashscreen_view import SplashscreenView
from views.workflow_view import WorkflowView

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Show the splash screen and start the Tkinter event loop.

    The root window is hidden until startup completes successfully.
    On failure the root is destroyed and the process exits cleanly.
    """
    # Hide main window — it will be revealed by _launch_main_app.
    root = tk.Tk()
    root.withdraw()

    # Build startup service from the configuration repository.
    config_file_path = get_current_working_directory() / C_APP_CONFIG_FILE
    config_repo = AppConfigurationRepository(config_file_path)
    startup_service = StartupService(config_repo)

    # Display splash screen and wire success/failure outcomes.
    splash_view = SplashscreenView(root)
    SplashscreenPresenter(
        view=splash_view,
        service=startup_service,
        on_success=lambda: _launch_main_app(root, config_repo, startup_service),
        on_failure=root.destroy,
    ).start()

    root.mainloop()


# ---------------------------------------------------------------------------
# Main application wiring
# ---------------------------------------------------------------------------


def _override_gui_and_style(root: tk.Tk, config_model: AppConfigurationModel) -> None:
    """Apply window title, geometry, fullscreen state, and global widget style.

    Args:
        root: The root Tk window to configure.
        config_model: Configuration model supplying sizing and style preferences.
    """
    root.title("Aspirabot")
    root.geometry(config_model.gui_booting_size)

    # Maximize on launch — behavior depends on the window manager.
    if config_model.gui_booting_fullscreen:
        if sys.platform.startswith("win"):
            root.state("zoomed")
        else:
            root.attributes("-zoomed", True)

    # Apply global padding to all ttk.Button widgets (style() -> Button())
    ttk.Style().configure("TButton", padding=(5, 5))


def _wire_all_navigation(
    main_view: MainView,
    provider_presenter: ProviderPresenter,
    provider_edit_presenter: WorkflowPresenter,
    scraping_presenter: ScrapingPresenter,
    history_presenter: HistoricPresenter,
) -> None:
    """Wire all inter-component navigation callbacks and lazy-loading hooks.

    Args:
        main_view: Navigation shell that controls tab visibility.
        provider_presenter: Presenter for the provider list view.
        provider_edit_presenter: Presenter for the provider edit view.
        scraping_presenter: Presenter for the scraping panel.
        history_presenter: Presenter for the history panel.
    """
    _wire_provider_navigation(main_view, provider_presenter, provider_edit_presenter)
    _wire_scraping_launch(main_view, provider_presenter, scraping_presenter)
    _wire_workflow_guard(main_view, provider_presenter, scraping_presenter)
    _wire_history_launch(main_view, history_presenter, scraping_presenter)
    main_view.set_on_show(TitleModuleEnum.E_EXECUTOR, scraping_presenter.ensure_providers_loaded)
    main_view.set_on_show(TitleModuleEnum.E_HISTORY, history_presenter.ensure_profiles_loaded)


def _build_and_wire_components(
    root: tk.Tk,
    main_view: MainView,
    config_repo: AppConfigurationRepository,
    startup_service: StartupService,
) -> None:
    """Instantiate all MVP groups, wire navigation, register views, and anchor presenters."""
    cfg = startup_service.config_model

    # Initialize each component group.
    log_view, log_p = _init_log_component(main_view, startup_service.logging_service, cfg.folder_logs)
    cfg_view, cfg_p = _init_config_component(main_view, config_repo)
    prov_view, prov_p, edit_view, edit_p, prov_svc = _init_provider_components(main_view, cfg)
    scr_view, scr_p = _init_scraping_component(main_view, cfg, prov_svc)
    hist_view, hist_p = _init_historic_components(main_view, cfg)
    dbg_view, dbg_p = _init_debug_component(main_view)

    # Wire navigation and finalize the window.
    _wire_all_navigation(main_view, prov_p, edit_p, scr_p, hist_p)
    _register_views(
        main_view,
        log_view,
        hist_view,
        cfg_view,
        prov_view,
        edit_view,
        scr_view,
        FaqView(main_view.content_area),
        dbg_view,
    )
    _anchor_presenters(root, [log_p, cfg_p, hist_p, prov_p, edit_p, scr_p, dbg_p])


def _launch_main_app(
    root: tk.Tk,
    config_repo: AppConfigurationRepository,
    startup_service: StartupService,
) -> None:
    """Configure and reveal the main window after startup succeeds."""
    _override_gui_and_style(root, startup_service.config_model)
    main_view = _build_main_view(root)
    _build_and_wire_components(root, main_view, config_repo, startup_service)
    root.deiconify()


def _build_main_view(root: tk.Tk) -> MainView:
    """Build and pack the sidebar-and-content layout inside the root window.

    Args:
        root: The root Tk window to embed the layout into.

    Returns:
        The initialized MainView instance.
    """
    root_container = tk.Frame(root)
    root_container.pack(fill=tk.BOTH, expand=True)
    main_view = MainView(root_container)
    main_view.pack(fill=tk.BOTH, expand=True)
    return main_view


# ---------------------------------------------------------------------------
# Component factories
# ---------------------------------------------------------------------------


def _init_log_component(
    main_view: MainView,
    logging_service: LoggingService,
    folder_logs: Path,
) -> tuple[LogView, LogPresenter]:
    """Create and wire the journal (log display) component.

    Args:
        main_view: Main container providing the content area as parent.
        logging_service: Service that broadcasts log events to the presenter.
        folder_logs: Path to the directory where log files are stored on disk.

    Returns:
        A (LogView, LogPresenter) tuple.
    """
    log_repository = LogRepository(folder_logs)
    log_view = LogView(main_view.content_area)
    # Presenter self-registers on logging_service via attach_ui_callback.
    log_presenter = LogPresenter(view=log_view, service=logging_service, repository=log_repository)
    return log_view, log_presenter


def _init_config_component(
    main_view: MainView,
    config_repo: AppConfigurationRepository,
) -> tuple[AppConfigurationView, AppConfigurationPresenter]:
    """Create and wire the application configuration component.

    Args:
        main_view: Main container providing the content area as parent.
        config_repo: Repository used for reading and persisting configuration.

    Returns:
        A (AppConfigurationView, AppConfigurationPresenter) tuple.
    """
    config_service = ConfigService(config_repo)
    config_view = AppConfigurationView(main_view.content_area)
    config_presenter = AppConfigurationPresenter(view=config_view, service=config_service)
    return config_view, config_presenter


def _init_historic_components(
    main_view: MainView,
    config_model: AppConfigurationModel,
) -> tuple[HistoricView, HistoricPresenter]:
    """Create and wire the historic component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the providers folder path.

    Returns:
        A (HistoricView, HistoricPresenter) tuple.
    """
    provider_repo = ProvidersRepository(config_model.folder_providers)
    historic_service = HistoricService(provider_repo)
    historic_view = HistoricView(main_view.content_area)
    historic_presenter = HistoricPresenter(view=historic_view, service=historic_service)
    return historic_view, historic_presenter


def _init_provider_components(
    main_view: MainView,
    config_model: AppConfigurationModel,
) -> tuple[
    ProvidersView,
    ProviderPresenter,
    WorkflowView,
    WorkflowPresenter,
    ProviderService,
]:
    """Create and wire the provider list and edit components.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the providers folder path.

    Returns:
        A (ProvidersListView, ProviderPresenter, ProviderEditView,
        ProviderEditPresenter, ProviderService) tuple.
    """
    # Shared service and repository for both list and edit sub-components.
    provider_repo = ProvidersRepository(config_model.folder_providers)
    provider_service = ProviderService(provider_repo)

    # Provider list view and presenter.
    provider_view = ProvidersView(main_view.content_area)
    provider_presenter = ProviderPresenter(view=provider_view, service=provider_service)

    # Provider edit view and presenter.
    provider_edit_view = WorkflowView(main_view.content_area)
    provider_edit_presenter = WorkflowPresenter(view=provider_edit_view, provider_service=provider_service)

    return provider_view, provider_presenter, provider_edit_view, provider_edit_presenter, provider_service


def _init_debug_component(
    main_view: MainView,
) -> tuple[DebugView, DebugPresenter]:
    """Create and wire the debug browser component.

    Args:
        main_view: Main container providing the content area as parent.

    Returns:
        A (DebugView, DebugPresenter) tuple.
    """
    debug_view = DebugView(main_view.content_area)
    debug_presenter = DebugPresenter(view=debug_view)
    return debug_view, debug_presenter


def _init_scraping_component(
    main_view: MainView,
    config_model: AppConfigurationModel,
    provider_service: ProviderService,
) -> tuple[ScrapingView, ScrapingPresenter]:
    """Create and wire the scraping panel component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scraping output folder.
        provider_service: The provider service for managing provider data.

    Returns:
        A (ScrapingPanelView, ScrapingPresenter) tuple.
    """
    workflow_service = WorkflowService()
    scraping_service = ScrapingService(config_model, workflow_service)
    scraping_view = ScrapingView(config_model, main_view.content_area)
    journal_repository = ScrapingJournalRepository()
    scraping_presenter = ScrapingPresenter(
        view=scraping_view,
        service_scraping=scraping_service,
        service_provider=provider_service,
        journal_repository=journal_repository,
    )
    return scraping_view, scraping_presenter


# ---------------------------------------------------------------------------
# Navigation wiring
# ---------------------------------------------------------------------------


def _wire_provider_navigation(
    main_view: MainView,
    provider_presenter: ProviderPresenter,
    provider_edit_presenter: WorkflowPresenter,
) -> None:
    """Connect create / edit / done navigation between provider views.

    Args:
        main_view: Shell managing tab visibility and enabled states.
        provider_presenter: Presenter for the provider list view.
        provider_edit_presenter: Presenter for the provider edit view.
    """

    def on_request_create_provider() -> None:
        # Open the edit form in creation mode and navigate to it.
        provider_edit_presenter.create_new()
        main_view.set_tab_state(TitleModuleEnum.E_EDITOR, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_SCRIPTS, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_HISTORY, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.DISABLED)
        main_view.show_view(TitleModuleEnum.E_EDITOR)

    def on_request_edit_provider(id_file: str) -> None:
        # Load the selected provider into the edit form and navigate to it.
        if provider_edit_presenter.load_provider(id_file):
            main_view.set_tab_state(TitleModuleEnum.E_EDITOR, tk.NORMAL)
            main_view.set_tab_state(TitleModuleEnum.E_SCRIPTS, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_HISTORY, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.DISABLED)
            main_view.show_view(TitleModuleEnum.E_EDITOR)

    def on_edit_done() -> None:
        # Return to the list and disable the edit tab after save/cancel.
        provider_presenter.refresh()
        main_view.set_tab_state(TitleModuleEnum.E_EDITOR, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_SCRIPTS, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_HISTORY, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_SCRIPTS)

    # Inject all navigation callbacks into the two presenters.
    provider_presenter.on_request_create_provider = on_request_create_provider
    provider_presenter.on_request_edit_provider = on_request_edit_provider
    provider_edit_presenter.set_on_done_callback(on_edit_done)

    # Initial state: workflow tab is disabled until a provider session is opened.
    main_view.set_tab_state(TitleModuleEnum.E_EDITOR, tk.DISABLED)


def _wire_scraping_launch(
    main_view: MainView,
    provider_presenter: ProviderPresenter,
    scraping_presenter: ScrapingPresenter,
) -> None:
    """Connect the launch action from the provider list to the scraping panel.

    Args:
        main_view: Shell managing tab visibility and enabled states.
        provider_presenter: Presenter that fires the launch request.
        provider_service: Service used to retrieve the full provider model by id.
        scraping_presenter: Presenter that loads and runs the scraping session.
    """

    def on_request_launch_provider(id_file: str) -> None:
        # Resolve the full provider model before handing off to scraping.
        scraping_presenter.load_provider(id_file)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_EXECUTOR)

    provider_presenter.on_request_launch_provider = on_request_launch_provider


def _wire_history_launch(
    main_view: MainView,
    historic_presenter: HistoricPresenter,
    scraping_presenter: ScrapingPresenter,
) -> None:
    """Connect the launch action from the historic list to the scraping panel.

    Args:
        main_view: Shell managing tab visibility.
        historic_presenter: Presenter that fires the launch request.
        scraping_presenter: Presenter that loads the provider and profile.
    """

    def on_request_launch_profile(id_provider: str, id_profile: str) -> None:
        # Load provider then select the specific profile before navigating.
        scraping_presenter.load_provider(id_provider)
        scraping_presenter.load_profile(id_profile)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_EXECUTOR)

    historic_presenter.on_request_launch_profile = on_request_launch_profile


def _wire_workflow_guard(
    main_view: MainView,
    provider_presenter: ProviderPresenter,
    scraping_presenter: ScrapingPresenter,
) -> None:
    """Inject the workflow-active guard into presenters that need it.

    The guard returns True when the Workflow tab is enabled (i.e. a provider
    creation or edit session is already in progress). Both ProviderPresenter and
    ScrapingPresenter use it to block conflicting actions and prompt the user.

    Args:
        main_view: Shell that owns the sidebar tab state.
        provider_presenter: Presenter for the providers list.
        scraping_presenter: Presenter for the scraping panel.
    """

    def is_workflow_active() -> bool:
        return main_view.get_tab_state(TitleModuleEnum.E_EDITOR) == tk.NORMAL

    # Inject into both presenters so either can check the guard independently.
    provider_presenter.is_workflow_active = is_workflow_active
    scraping_presenter.is_workflow_active = is_workflow_active


# ---------------------------------------------------------------------------
# View registration
# ---------------------------------------------------------------------------


def _register_views(
    main_view: MainView,
    log_view: LogView,
    historic_view: HistoricView,
    config_view: AppConfigurationView,
    provider_view: ProvidersView,
    provider_edit_view: WorkflowView,
    scraping_view: ScrapingView,
    faq_view: FaqView,
    debug_view: DebugView,
) -> None:
    """Map each sidebar entry to its view widget and show the default tab."""
    # Map each sidebar label to its corresponding view widget.
    main_view.add_view(TitleModuleEnum.E_LOGS, log_view)
    main_view.add_view(TitleModuleEnum.E_HISTORY, historic_view)
    main_view.add_view(TitleModuleEnum.E_SCRIPTS, provider_view)
    main_view.add_view(TitleModuleEnum.E_EDITOR, provider_edit_view)
    main_view.add_view(TitleModuleEnum.E_EXECUTOR, scraping_view)
    main_view.add_view(TitleModuleEnum.E_FAQ, faq_view)
    main_view.add_view(TitleModuleEnum.E_OPTIONS, config_view)
    main_view.add_view(TitleModuleEnum.E_DEBUG, debug_view)

    # Land on the providers list as the startup default.
    main_view.show_view(TitleModuleEnum.E_SCRIPTS)


def _anchor_presenters(root: tk.Tk, presenters: list[object]) -> None:
    """Attach presenters to the root window to prevent garbage collection.

    Args:
        root: The root Tk window that outlives all presenters.
        presenters: Presenter instances to keep alive for the application lifetime.
    """
    root._app_presenters = presenters


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()

# EOF
