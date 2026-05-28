"""Application entry point for Aspirabot."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk

import models.steps  # noqa: F401 - load registry entries
import services.steps  # noqa: F401 - load registry entries
import views.steps  # noqa: F401 - load registry entries
from models.app_configuration_model import AppConfigurationModel
from presenters.app_configuration_presenter import AppConfigurationPresenter
from presenters.debug_presenter import DebugPresenter
from presenters.executor_presenter import ExecutorPresenter
from presenters.log_presenter import LogPresenter
from presenters.profiles_presenter import ProfilesPresenter
from presenters.scenarios_presenter import ScenariosPresenter
from presenters.scraping_presenter import ScrapingPresenter
from presenters.splashscreen_presenter import SplashscreenPresenter
from presenters.workflow_presenter import WorkflowPresenter
from repositories.app_configuration_repository import AppConfigurationRepository
from repositories.journal_repository import JournalRepository
from repositories.json_repository import JsonFileRepository
from repositories.profiles_repository import ProfilesRepository
from repositories.scenarios_repository import ScenariosRepository
from services.app_configuration_service import ConfigService
from services.browser_playwright_service import BrowserPlaywrightService
from services.debug_browser_service import DebugBrowserService
from services.logging_service import LoggingService
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.scraping_service import ScrapingService
from services.startup_service import StartupService
from services.workflow_service import WorkflowService

# Bootstrap: import all step packages to populate the central registry.
from shared.constants import C_APP_CONFIG_FILE
from shared.i18n_fra import TitleModuleEnum
from shared.path_util import get_current_working_directory
from views.app_configuration_view import AppConfigurationView
from views.debug_view import DebugView
from views.executor_view import ExecutorView
from views.faq_view import FaqView
from views.log_view import LogView
from views.main_view import MainView
from views.profiles_view import ProfilesView
from views.scenarios_view import ScenariosView
from views.scraping_view import ScrapingView
from views.splashscreen_view import SplashscreenView
from views.workflow_view import WorkflowView

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Main application wiring
# -----------------------------------------------------------------------------


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
    scenario_presenter: ScenariosPresenter,
    workflow_presenter: WorkflowPresenter,
    executor_presenter: ExecutorPresenter,
    profiles_presenter: ProfilesPresenter,
    scraping_presenter: ScrapingPresenter,
) -> None:
    """Wire all inter-component navigation callbacks and lazy-loading hooks.

    Args:
        main_view: Navigation shell that controls tab visibility.
        scenario_presenter: Presenter for the scenario list view.
        workflow_presenter: Presenter for the scenario edit view.
        executor_presenter: Presenter for the executor panel.
        profiles_presenter: Presenter for the profiles panel.
        scraping_presenter: Presenter for the live scraping panel.
    """
    _wire_scenario_navigation(main_view, scenario_presenter, workflow_presenter)
    _wire_executor_launch(main_view, scenario_presenter, executor_presenter)
    _wire_profiles_launch(main_view, profiles_presenter, executor_presenter)
    _wire_scraping_navigation(main_view, executor_presenter, scraping_presenter)

    def on_executor_edit_scenario(id_file: str) -> None:
        if workflow_presenter.load_scenario(id_file):
            main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.NORMAL)
            main_view.set_tab_state(TitleModuleEnum.E_SCENARIOS, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_PROFILES, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_SCRAPING, tk.DISABLED)
            main_view.show_view(TitleModuleEnum.E_WORKFLOW)

    executor_presenter.on_request_edit_scenario = on_executor_edit_scenario
    main_view.set_on_show(TitleModuleEnum.E_PROFILES, profiles_presenter.ensure_profiles_loaded)
    main_view.set_on_show(TitleModuleEnum.E_EXECUTOR, executor_presenter.ensure_scenarios_loaded)


def _build_and_wire_components(  # noqa: PLR0914
    root: tk.Tk, main_view: MainView, config_repo: AppConfigurationRepository, startup_service: StartupService
) -> None:
    """Instantiate all MVP groups, wire navigation, register views, and anchor presenters."""
    # Initialize each component group.
    # JsonFileRepository instances share a class-level cache, so passing two
    # separate instances to provider and historic components is functionally
    # equivalent to sharing one — both benefit from the same cached data.
    log_view, log_pr = _init_log_component(main_view, startup_service.logging_service)
    cfg_view, cfg_pr = _init_config_component(main_view, config_repo)
    profiles_view, prof_pr, prof_svc = _init_profiles_components(
        main_view, startup_service.config_model, JsonFileRepository()
    )
    scen_view, scen_pre, edit_view, edit_p, scen_svc = _init_scenarios_components(
        main_view, prof_svc, startup_service.config_model, JsonFileRepository()
    )
    exec_view, exec_pre = _init_executor_component(main_view, startup_service.config_model, scen_svc, prof_svc)
    scrap_view, scrap_pre = _init_scraping_component(main_view, startup_service.config_model)
    dbg_view, dbg_p = _init_debug_component(main_view)

    # Wire navigation and finalize the window.
    _wire_all_navigation(main_view, scen_pre, edit_p, exec_pre, prof_pr, scrap_pre)
    _register_views(
        main_view,
        log_view,
        profiles_view,
        cfg_view,
        scen_view,
        edit_view,
        exec_view,
        scrap_view,
        FaqView(main_view.content_area),
        dbg_view,
    )
    _anchor_presenters(root, [log_pr, cfg_pr, prof_pr, scen_pre, edit_p, exec_pre, dbg_p])


def _launch_main_app(root: tk.Tk, config_repo: AppConfigurationRepository, startup_service: StartupService) -> None:
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


# -----------------------------------------------------------------------------
# Component factories
# -----------------------------------------------------------------------------


def _init_log_component(main_view: MainView, logging_service: LoggingService) -> tuple[LogView, LogPresenter]:
    """Create and wire the journal (log display) component.

    Args:
        main_view: Main container providing the content area as parent.
        logging_service: Service that stores entries and broadcasts log events.

    Returns:
        A (LogView, LogPresenter) tuple.
    """
    log_view = LogView(main_view.content_area)
    # Presenter self-registers on logging_service via attach_ui_callback.
    log_presenter = LogPresenter(view=log_view, service=logging_service)
    return log_view, log_presenter


def _init_config_component(
    main_view: MainView, config_repo: AppConfigurationRepository
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


def _init_profiles_components(
    main_view: MainView, config_model: AppConfigurationModel, json_repo: JsonFileRepository
) -> tuple[ProfilesView, ProfilesPresenter, ProfilesService]:
    """Create and wire the historic component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scenarios folder path.
        json_repo: Shared JSON repository injected into the scenarios repository.

    Returns:
        A (ProfilesView, ProfilesPresenter, ProfilesService) tuple.
    """
    repo = ProfilesRepository(config_model.folder_scenarios, json_repo)
    service = ProfilesService(repo)
    view = ProfilesView(main_view.content_area)
    presenter = ProfilesPresenter(view=view, service=service)
    return view, presenter, service


def _init_scenarios_components(
    main_view: MainView,
    profiles_service: ProfilesService,
    config_model: AppConfigurationModel,
    json_repo: JsonFileRepository,
) -> tuple[ScenariosView, ScenariosPresenter, WorkflowView, WorkflowPresenter, ScenariosService]:
    """Create and wire the scenario list and edit components.

    Args:
        main_view: Main container providing the content area as parent.
        profiles_service: Service for managing profile data.
        config_model: Configuration model supplying the scenarios folder path.
        json_repo: Shared JSON repository injected into the scenarios repository.

    Returns:
        A (ScenariosView, ScenariosPresenter, WorkflowView,
        WorkflowPresenter, ScenariosService) tuple.
    """
    scenario_repo = ScenariosRepository(config_model.folder_scenarios, json_repo)
    scenarios_service = ScenariosService(scenario_repo)

    scenario_view = ScenariosView(main_view.content_area)
    scenario_presenter = ScenariosPresenter(view=scenario_view, service=scenarios_service)

    workflow_view = WorkflowView(main_view.content_area)
    workflow_presenter = WorkflowPresenter(workflow_view, scenarios_service, profiles_service, WorkflowService())

    return scenario_view, scenario_presenter, workflow_view, workflow_presenter, scenarios_service


def _init_debug_component(main_view: MainView) -> tuple[DebugView, DebugPresenter]:
    """Create and wire the debug browser component.

    Args:
        main_view: Main container providing the content area as parent.

    Returns:
        A (DebugView, DebugPresenter) tuple.
    """
    debug_view = DebugView(main_view.content_area)
    debug_presenter = DebugPresenter(view=debug_view, debug_service=DebugBrowserService())
    return debug_view, debug_presenter


def _init_executor_component(
    main_view: MainView,
    config_model: AppConfigurationModel,
    scenario_service: ScenariosService,
    profiles_service: ProfilesService,
) -> tuple[ExecutorView, ExecutorPresenter]:
    """Create and wire the executor panel component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the executor output folder.
        scenario_service: The scenario service for managing scenario data.
        profiles_service: The profiles service for managing profile data.

    Returns:
        A (ExecutorView, ExecutorPresenter) tuple.
    """
    executor_view = ExecutorView(main_view.content_area)
    executor_presenter = ExecutorPresenter(
        view=executor_view, scenarios_service=scenario_service, profiles_service=profiles_service
    )
    return executor_view, executor_presenter


def _init_scraping_component(
    main_view: MainView, config_model: AppConfigurationModel
) -> tuple[ScrapingView, ScrapingPresenter]:
    """Create and wire the scraping panel component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scraping output folder.

    Returns:
        A (ScrapingView, ScrapingPresenter) tuple.
    """
    scraping_view = ScrapingView(main_view.content_area)
    scraping_service = ScrapingService(
        model_config=config_model,
        workflow_service=WorkflowService(),
        extracted_data_repository=JsonFileRepository(),
        browser_service_factory=BrowserPlaywrightService,
        journal_repository=JournalRepository(),
    )
    scraping_presenter = ScrapingPresenter(view=scraping_view, service=scraping_service)
    return scraping_view, scraping_presenter


# -----------------------------------------------------------------------------
# Navigation wiring
# -----------------------------------------------------------------------------


def _wire_scenario_navigation(
    main_view: MainView, scenario_presenter: ScenariosPresenter, workflow_presenter: WorkflowPresenter
) -> None:
    """Connect create / edit / done navigation between views.

    Args:
        main_view: Shell managing tab visibility and enabled states.
        scenario_presenter: Presenter for the scenario list view.
        workflow_presenter: Presenter for the scenario edit view.
    """

    def on_request_create_scenario() -> None:
        # Open the edit form in creation mode and navigate to it.
        workflow_presenter.create_new()
        main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_SCENARIOS, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_PROFILES, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_SCRAPING, tk.DISABLED)
        main_view.show_view(TitleModuleEnum.E_WORKFLOW)

    def on_request_edit_scenario(id_file: str) -> None:
        # Load the selected into the edit form and navigate to it.
        if workflow_presenter.load_scenario(id_file):
            main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.NORMAL)
            main_view.set_tab_state(TitleModuleEnum.E_SCENARIOS, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_PROFILES, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_SCRAPING, tk.DISABLED)
            main_view.show_view(TitleModuleEnum.E_WORKFLOW)

    def on_edit_done() -> None:
        # Return to the list and disable the edit tab after save/cancel.
        scenario_presenter.ensure_profiles_loaded()
        main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.DISABLED)
        main_view.set_tab_state(TitleModuleEnum.E_SCENARIOS, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_PROFILES, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_SCRAPING, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_SCENARIOS)

    # Inject all navigation callbacks into the two presenters.
    scenario_presenter.on_request_create_scenario = on_request_create_scenario
    scenario_presenter.on_request_edit_scenario = on_request_edit_scenario
    workflow_presenter.set_on_done_callback(on_edit_done)

    # Initial state: workflow tab is disabled
    main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.DISABLED)


def _wire_scraping_navigation(
    main_view: MainView, executor_presenter: ExecutorPresenter, scraping_presenter: ScrapingPresenter
) -> None:
    """Connect executor launch to the scraping panel and wire start/stop hooks.

    Args:
        main_view: Shell managing tab visibility.
        executor_presenter: Source of the launch request.
        scraping_presenter: Target that runs the session.
    """
    blocked_mods = (
        TitleModuleEnum.E_PROFILES,
        TitleModuleEnum.E_SCENARIOS,
        TitleModuleEnum.E_EXECUTOR,
        TitleModuleEnum.E_WORKFLOW,
    )

    def on_scraping_started() -> None:
        for mod in blocked_mods:
            main_view.set_tab_state(mod, tk.DISABLED)

    def on_scraping_stopped() -> None:
        for mod in blocked_mods:
            main_view.set_tab_state(mod, tk.NORMAL)

    def on_request_launch_scraping(scenario: object, profile: object) -> None:
        scraping_presenter.set_launch_context(scenario, profile)  # type: ignore[arg-type]
        main_view.set_tab_state(TitleModuleEnum.E_SCRAPING, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_SCRAPING)
        scraping_presenter.start_scraping()

    scraping_presenter.on_scraping_started = on_scraping_started
    scraping_presenter.on_scraping_stopped = on_scraping_stopped
    executor_presenter.on_request_launch_scraping = on_request_launch_scraping


def _wire_executor_launch(
    main_view: MainView, scenario_presenter: ScenariosPresenter, executor_presenter: ExecutorPresenter
) -> None:
    """Connect the launch action from the scenario list to the executor panel.

    Args:
        main_view: Shell managing tab visibility and enabled states.
        scenario_presenter: Presenter that fires the launch request.
        scenario_service: Service used to retrieve the full provider model by id.
        executor_presenter: Presenter that loads and runs the executor session.
    """

    def on_request_launch_scenario(id_file: str) -> None:
        executor_presenter.load_scenario(id_file)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_EXECUTOR)

    scenario_presenter.on_request_launch_scenario = on_request_launch_scenario


def _wire_profiles_launch(
    main_view: MainView, historic_presenter: ProfilesPresenter, executor_presenter: ExecutorPresenter
) -> None:
    """Connect the launch action from the historic list to the executor panel.

    Args:
        main_view: Shell managing tab visibility.
        historic_presenter: Presenter that fires the launch request.
        executor_presenter: Presenter that loads the scenario and profile.
    """

    def on_request_launch_profile(id_scenario: str, id_profile: str) -> None:
        executor_presenter.load_scenario_and_profile(id_scenario, id_profile)
        main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.NORMAL)
        main_view.show_view(TitleModuleEnum.E_EXECUTOR)

    historic_presenter.on_request_launch_profile = on_request_launch_profile


# -----------------------------------------------------------------------------
# View registration
# -----------------------------------------------------------------------------


def _register_views(  # noqa: PLR0913, PLR0917
    main_view: MainView,
    log_view: LogView,
    historic_view: ProfilesView,
    config_view: AppConfigurationView,
    scenario_view: ScenariosView,
    workflow_view: WorkflowView,
    executor_view: ExecutorView,
    scraping_view: ScrapingView,
    faq_view: FaqView,
    debug_view: DebugView,
) -> None:
    """Map each sidebar entry to its view widget and show the default tab."""
    # Map each sidebar label to its corresponding view widget.
    main_view.add_view(TitleModuleEnum.E_LOGS, log_view)
    main_view.add_view(TitleModuleEnum.E_PROFILES, historic_view)
    main_view.add_view(TitleModuleEnum.E_SCENARIOS, scenario_view)
    main_view.add_view(TitleModuleEnum.E_WORKFLOW, workflow_view)
    main_view.add_view(TitleModuleEnum.E_EXECUTOR, executor_view)
    main_view.add_view(TitleModuleEnum.E_SCRAPING, scraping_view)
    main_view.add_view(TitleModuleEnum.E_FAQ, faq_view)
    main_view.add_view(TitleModuleEnum.E_OPTIONS, config_view)
    main_view.add_view(TitleModuleEnum.E_DEBUG, debug_view)

    # Land on the scenarios list as the startup default.
    main_view.show_view(TitleModuleEnum.E_SCENARIOS)


def _anchor_presenters(root: tk.Tk, presenters: list[object]) -> None:
    """Attach presenters to the root window to prevent garbage collection.

    Args:
        root: The root Tk window that outlives all presenters.
        presenters: Presenter instances to keep alive for the application lifetime.
    """
    root._app_presenters = presenters


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()

# EOF
