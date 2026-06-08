"""Application entry point for Aspirabot."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk

import models.steps  # noqa: F401 - load registry entries
import presenters.steps  # noqa: F401 - load registry entries (params builders)
import services.steps  # noqa: F401 - load registry entries
import views.steps  # noqa: F401 - load registry entries
from models.app_configuration_model import AppConfigurationModel
from presenters.app_configuration_presenter import AppConfigurationPresenter
from presenters.debug_presenter import DebugPresenter
from presenters.discover_presenter import DiscoverPresenter
from presenters.executor_presenter import ExecutorPresenter
from presenters.log_presenter import LogPresenter
from presenters.profiles_presenter import ProfilesPresenter
from presenters.scenarios_presenter import ScenariosPresenter
from presenters.scraping_presenter import ScrapingPresenter
from presenters.splashscreen_presenter import SplashscreenPresenter
from presenters.steps_list_presenter import StepsListPresenter
from presenters.workflow_presenter import WorkflowPresenter
from repositories.app_configuration_repository import AppConfigurationRepository
from repositories.discover_repository import DiscoverRepository
from repositories.journal_repository import JournalRepository
from repositories.json_repository import JsonFileRepository
from repositories.profiles_repository import ProfilesRepository
from repositories.scenarios_repository import ScenariosRepository
from services.app_configuration_service import ConfigService
from services.browser_playwright_service import BrowserPlaywrightService
from services.debug_browser_service import DebugBrowserService
from services.discover_service import DiscoverService
from services.logging_service import LoggingService
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.scraping_service import ScrapingService
from services.startup_service import StartupService
from services.workflow_service import WorkflowService

# Bootstrap: import all step packages to populate the central registry.
from shared.constants import C_APP_CONFIG_FILE
from shared.enums import TitleModuleEnum
from shared.path_util import get_current_working_directory
from view_models.app_configuration_view_model import AppConfigurationViewModel
from view_models.debug_view_model import DebugViewModel
from view_models.discover_view_model import DiscoverViewModel
from view_models.executor_view_model import ExecutorViewModel
from view_models.log_view_model import LogViewModel
from view_models.profiles_view_model import ProfilesViewModel
from view_models.scenarios_view_model import ScenariosViewModel
from view_models.scraping_view_model import ScrapingViewModel
from view_models.splashscreen_view_model import SplashscreenViewModel
from view_models.workflow_view_model import WorkflowViewModel
from views.app_configuration_view import AppConfigurationView
from views.debug_view import DebugView
from views.discover_view import DiscoverView
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
    root = tk.Tk()
    root.withdraw()

    config_file_path = get_current_working_directory() / C_APP_CONFIG_FILE
    config_repo = AppConfigurationRepository(config_file_path)
    startup_service = StartupService(config_repo)

    # Build ViewModel before the View so both receive the same instance.
    splash_vm = SplashscreenViewModel(master=root)
    _splash_view = SplashscreenView(root, vm=splash_vm)
    SplashscreenPresenter(
        vm=splash_vm,
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

    if config_model.gui_booting_fullscreen:
        if sys.platform.startswith("win"):
            root.state("zoomed")
        else:
            root.attributes("-zoomed", True)  # type: ignore[reportUnknownMemberType]

    ttk.Style().configure("TButton", padding=(5, 5))


def _wire_all_navigation(
    main_view: MainView,
    scenario_presenter: ScenariosPresenter,
    workflow_presenter: WorkflowPresenter,
    executor_presenter: ExecutorPresenter,
    profiles_presenter: ProfilesPresenter,
    scraping_presenter: ScrapingPresenter,
    discover_presenter: DiscoverPresenter,
) -> None:
    """Wire all inter-component navigation callbacks and lazy-loading hooks.

    Args:
        main_view: Navigation shell that controls tab visibility.
        scenario_presenter: Presenter for the scenario list view.
        workflow_presenter: Presenter for the scenario edit view.
        executor_presenter: Presenter for the executor panel.
        profiles_presenter: Presenter for the profiles panel.
        scraping_presenter: Presenter for the live scraping panel.
        discover_presenter: Presenter for the discover panel.
    """
    _wire_scenario_navigation(main_view, scenario_presenter, workflow_presenter)
    _wire_executor_launch(main_view, scenario_presenter, executor_presenter)
    _wire_profiles_launch(main_view, profiles_presenter, executor_presenter)
    _wire_scraping_navigation(main_view, executor_presenter, scraping_presenter)

    def on_executor_edit_scenario(id_file: str) -> None:
        if workflow_presenter.load_scenario(id_file):
            main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.NORMAL)
            main_view.set_tab_state(TitleModuleEnum.E_SCENARIOS, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_DISCOVER, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_PROFILES, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_EXECUTOR, tk.DISABLED)
            main_view.set_tab_state(TitleModuleEnum.E_SCRAPING, tk.DISABLED)
            main_view.show_view(TitleModuleEnum.E_WORKFLOW)

    executor_presenter.on_request_edit_scenario = on_executor_edit_scenario
    main_view.set_on_show(TitleModuleEnum.E_PROFILES, profiles_presenter.ensure_profiles_loaded)
    main_view.set_on_show(TitleModuleEnum.E_EXECUTOR, executor_presenter.ensure_scenarios_loaded)
    main_view.set_on_show(TitleModuleEnum.E_DISCOVER, discover_presenter.ensure_data_loaded)


def _build_and_wire_components(  # noqa: PLR0914
    root: tk.Tk, main_view: MainView, config_repo: AppConfigurationRepository, startup_service: StartupService
) -> None:
    """Instantiate all MVP groups, wire navigation, register views, and anchor presenters."""
    log_view, log_pr = _init_log_component(main_view, startup_service.logging_service)
    cfg_view, cfg_pr = _init_config_component(main_view, config_repo)
    profiles_view, prof_pr, prof_svc, prof_repo = _init_profiles_components(
        main_view, startup_service.config_model, JsonFileRepository()
    )
    scen_view, scen_pre, edit_view, edit_pr, steps_pr, scen_svc = _init_scenarios_components(
        main_view, prof_svc, prof_repo, startup_service.config_model, JsonFileRepository()
    )
    exec_view, exec_pre = _init_executor_component(main_view, startup_service.config_model, scen_svc, prof_svc)
    scrap_view, scrap_pre = _init_scraping_component(main_view, startup_service.config_model, scen_svc)
    dbg_view, dbg_p = _init_debug_component(main_view, startup_service.config_model)
    disc_view, disc_pr = _init_discover_component(
        main_view, startup_service.config_model, prof_svc, JsonFileRepository()
    )
    _wire_all_navigation(main_view, scen_pre, edit_pr, exec_pre, prof_pr, scrap_pre, disc_pr)
    views: list[tk.Widget] = [
        log_view,
        profiles_view,
        cfg_view,
        scen_view,
        edit_view,
        exec_view,
        scrap_view,
        dbg_view,
        disc_view,
    ]
    presenters: list[object] = [
        log_pr,
        cfg_pr,
        prof_pr,
        scen_pre,
        edit_pr,
        steps_pr,
        exec_pre,
        scrap_pre,
        dbg_p,
        disc_pr,
    ]
    _register_and_anchor(root, main_view, views, presenters)


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
    log_vm = LogViewModel(master=main_view.content_area)
    log_view = LogView(main_view.content_area, vm=log_vm)
    log_presenter = LogPresenter(vm=log_vm, service=logging_service)
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
    config_vm = AppConfigurationViewModel(master=main_view.content_area)
    config_view = AppConfigurationView(main_view.content_area, vm=config_vm)
    config_presenter = AppConfigurationPresenter(vm=config_vm, service=config_service)
    return config_view, config_presenter


def _init_profiles_components(
    main_view: MainView, config_model: AppConfigurationModel, json_repo: JsonFileRepository
) -> tuple[ProfilesView, ProfilesPresenter, ProfilesService, ProfilesRepository]:
    """Create and wire the historic component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scenarios folder path.
        json_repo: Shared JSON repository injected into the scenarios repository.

    Returns:
        A (ProfilesView, ProfilesPresenter, ProfilesService, ProfilesRepository) tuple.
        The repository is returned so callers can inject it into other services directly.
    """
    repo = ProfilesRepository(config_model.folder_scenarios, json_repo)
    service = ProfilesService(repo)
    profiles_vm = ProfilesViewModel(master=main_view.content_area)
    view = ProfilesView(main_view.content_area, vm=profiles_vm)
    presenter = ProfilesPresenter(vm=profiles_vm, service=service)
    return view, presenter, service, repo


def _init_scenarios_components(
    main_view: MainView,
    profiles_service: ProfilesService,
    profiles_repo: ProfilesRepository,
    config_model: AppConfigurationModel,
    json_repo: JsonFileRepository,
) -> tuple[ScenariosView, ScenariosPresenter, WorkflowView, WorkflowPresenter, StepsListPresenter, ScenariosService]:
    """Create and wire the scenario list and edit components.

    Args:
        main_view: Main container providing the content area as parent.
        profiles_service: Service for managing profile data.
        profiles_repo: Repository for profile data, injected directly to avoid
            accessing private attributes of ProfilesService.
        config_model: Configuration model supplying the scenarios folder path.
        json_repo: Shared JSON repository injected into the scenarios repository.

    Returns:
        A (ScenariosView, ScenariosPresenter, WorkflowView, WorkflowPresenter,
        StepsListPresenter, ScenariosService) tuple.
    """
    scenario_repo = ScenariosRepository(config_model.folder_scenarios, json_repo)
    scenarios_service = ScenariosService(scenario_repo, profiles_repo)
    scenarios_vm = ScenariosViewModel(master=main_view.content_area)
    scenario_view = ScenariosView(main_view.content_area, vm=scenarios_vm)
    scenario_presenter = ScenariosPresenter(vm=scenarios_vm, service=scenarios_service)
    workflow_view, workflow_presenter, steps_list_presenter = _init_workflow_group(
        main_view, scenarios_service, profiles_service
    )
    return (
        scenario_view,
        scenario_presenter,
        workflow_view,
        workflow_presenter,
        steps_list_presenter,
        scenarios_service,
    )


def _init_workflow_group(
    main_view: MainView, scenarios_service: ScenariosService, profiles_service: ProfilesService
) -> tuple[WorkflowView, WorkflowPresenter, StepsListPresenter]:
    """Instantiate the workflow view, presenter, and steps-list presenter.

    Args:
        main_view: Main container providing the content area as parent.
        scenarios_service: Shared scenarios service injected into workflow components.
        profiles_service: Shared profiles service injected into the WorkflowPresenter.

    Returns:
        A (WorkflowView, WorkflowPresenter, StepsListPresenter) tuple.
    """
    workflow_svc = WorkflowService()
    workflow_vm = WorkflowViewModel(master=main_view.content_area)
    workflow_view = WorkflowView(main_view.content_area, vm=workflow_vm)
    # StepsListPresenter instantiated here (composition root) and injected into
    # WorkflowPresenter — never created inside another presenter.
    steps_list_presenter = StepsListPresenter(
        view=workflow_view.workflow_builder_view,
        service_scenario=scenarios_service,
        workflow_service=workflow_svc,
        gestion_view=workflow_view,
    )
    workflow_presenter = WorkflowPresenter(
        vm=workflow_vm,
        scenarios_service=scenarios_service,
        profiles_service=profiles_service,
        workflow_service=workflow_svc,
        steps_list_presenter=steps_list_presenter,
    )
    return workflow_view, workflow_presenter, steps_list_presenter


def _init_debug_component(main_view: MainView, config_model: AppConfigurationModel) -> tuple[DebugView, DebugPresenter]:
    """Create and wire the debug browser component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Application configuration supplying Chromium paths.

    Returns:
        A (DebugView, DebugPresenter) tuple.
    """
    debug_vm = DebugViewModel(master=main_view.content_area)
    debug_view = DebugView(main_view.content_area, vm=debug_vm)
    debug_presenter = DebugPresenter(vm=debug_vm, debug_service=DebugBrowserService(), config_model=config_model)
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
    vm = ExecutorViewModel(master=main_view.content_area)
    executor_view = ExecutorView(main_view.content_area, vm=vm)
    executor_presenter = ExecutorPresenter(vm=vm, scenarios_service=scenario_service, profiles_service=profiles_service)
    return executor_view, executor_presenter


def _init_scraping_component(
    main_view: MainView, config_model: AppConfigurationModel, scenarios_service: ScenariosService
) -> tuple[ScrapingView, ScrapingPresenter]:
    """Create and wire the scraping panel component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scraping output folder.
        scenarios_service: The scenarios service for managing scenario data.

    Returns:
        A (ScrapingView, ScrapingPresenter) tuple.
    """
    scraping_vm = ScrapingViewModel(master=main_view.content_area)
    scraping_view = ScrapingView(main_view.content_area, vm=scraping_vm)
    scraping_service = ScrapingService(
        model_config=config_model,
        workflow_service=WorkflowService(),
        extracted_data_repository=JsonFileRepository(),
        browser_service_factory=lambda: BrowserPlaywrightService(
            chromium_persistant_dir=config_model.chromium_persistant_dir,
            chromium_extensions_dir=config_model.chromium_extensions_dir,
        ),
        journal_repository=JournalRepository(),
    )
    scraping_presenter = ScrapingPresenter(scraping_vm, scraping_service, scenarios_service)
    return scraping_view, scraping_presenter


def _init_discover_component(
    main_view: MainView,
    config_model: AppConfigurationModel,
    profiles_service: ProfilesService,
    json_repo: JsonFileRepository,
) -> tuple[DiscoverView, DiscoverPresenter]:
    """Create and wire the Discover module component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scenarios folder path.
        profiles_service: Shared profiles service used to list and update profiles.
        json_repo: Shared JSON repository injected into the discover repository.

    Returns:
        A (DiscoverView, DiscoverPresenter) tuple.
    """
    repo = DiscoverRepository(config_model.folder_scenarios, json_repo)
    service = DiscoverService(repo)
    vm = DiscoverViewModel(master=main_view.content_area)
    presenter = DiscoverPresenter(vm=vm, service=service, profiles_service=profiles_service)
    view = DiscoverView(main_view.content_area, vm=vm, presenter=presenter)
    return view, presenter


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
        workflow_presenter.create_new()
        _open_workflow_tab(main_view)

    def on_request_edit_scenario(id_file: str) -> None:
        if workflow_presenter.load_scenario(id_file):
            _open_workflow_tab(main_view)

    def on_edit_done() -> None:
        scenario_presenter.ensure_profiles_loaded()
        _close_workflow_tab(main_view)

    scenario_presenter.on_request_create_scenario = on_request_create_scenario
    scenario_presenter.on_request_edit_scenario = on_request_edit_scenario
    workflow_presenter.set_on_done_callback(on_edit_done)
    main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.DISABLED)


def _open_workflow_tab(main_view: MainView) -> None:
    """Enable the workflow tab and disable sibling tabs.

    Args:
        main_view: Navigation shell managing tab visibility.
    """
    main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.NORMAL)
    for mod in (
        TitleModuleEnum.E_SCENARIOS,
        TitleModuleEnum.E_PROFILES,
        TitleModuleEnum.E_DISCOVER,
        TitleModuleEnum.E_EXECUTOR,
        TitleModuleEnum.E_SCRAPING,
    ):
        main_view.set_tab_state(mod, tk.DISABLED)
    main_view.show_view(TitleModuleEnum.E_WORKFLOW)


def _close_workflow_tab(main_view: MainView) -> None:
    """Disable the workflow tab and re-enable sibling tabs.

    Args:
        main_view: Navigation shell managing tab visibility.
    """
    main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.DISABLED)
    for mod in (
        TitleModuleEnum.E_SCENARIOS,
        TitleModuleEnum.E_PROFILES,
        TitleModuleEnum.E_DISCOVER,
        TitleModuleEnum.E_EXECUTOR,
        TitleModuleEnum.E_SCRAPING,
    ):
        main_view.set_tab_state(mod, tk.NORMAL)
    main_view.show_view(TitleModuleEnum.E_SCENARIOS)


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
        TitleModuleEnum.E_DISCOVER,
        TitleModuleEnum.E_EXECUTOR,
        TitleModuleEnum.E_WORKFLOW,
    )

    def on_scraping_started() -> None:
        for mod in blocked_mods:
            main_view.set_tab_state(mod, tk.DISABLED)

    def on_scraping_stopped() -> None:
        for mod in blocked_mods:
            main_view.set_tab_state(mod, tk.NORMAL)
        main_view.set_tab_state(TitleModuleEnum.E_WORKFLOW, tk.DISABLED)

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


def _register_and_anchor(root: tk.Tk, main_view: MainView, views: list[tk.Widget], presenters: list[object]) -> None:
    """Unpack the ordered view list, register all views, anchor presenters, and wire teardown.

    Args:
        root: Root window used as GC anchor for all presenters.
        main_view: Navigation shell that maps modules to view widgets.
        views: Ordered list [log, profiles, cfg, scenarios, workflow, executor, scraping, debug, discover].
        presenters: All presenter instances to keep alive for the application lifetime.
    """
    log_v, prof_v, cfg_v, scen_v, wf_v, exec_v, scrap_v, dbg_v, disc_v = views
    faq_v = FaqView(main_view.content_area)
    _register_views(main_view, log_v, prof_v, cfg_v, scen_v, wf_v, exec_v, scrap_v, faq_v, dbg_v, disc_v)  # type: ignore[arg-type]
    _anchor_presenters(root, presenters)
    # Register teardown sequence on application close.
    _wire_teardown(root, [log_v, prof_v, cfg_v, scen_v, wf_v, exec_v, scrap_v, dbg_v, disc_v])


def _wire_teardown(root: tk.Tk, teardown_views: list[tk.Widget]) -> None:
    """Register WM_DELETE_WINDOW to call teardown() on each View before destroying root.

    Teardown order: each View removes its VM traces and disposes its ViewModel,
    then root is destroyed.

    Args:
        root: The root Tk window.
        teardown_views: Views that implement ``teardown()``; called in list order.
    """

    def _on_close() -> None:
        for view in teardown_views:
            teardown_fn = getattr(view, "teardown", None)
            if callable(teardown_fn):
                teardown_fn()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)


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
    discover_view: DiscoverView,
) -> None:
    """Map each sidebar entry to its view widget and show the default tab."""
    main_view.add_view(TitleModuleEnum.E_LOGS, log_view)
    main_view.add_view(TitleModuleEnum.E_PROFILES, historic_view)
    main_view.add_view(TitleModuleEnum.E_SCENARIOS, scenario_view)
    main_view.add_view(TitleModuleEnum.E_WORKFLOW, workflow_view)
    main_view.add_view(TitleModuleEnum.E_EXECUTOR, executor_view)
    main_view.add_view(TitleModuleEnum.E_SCRAPING, scraping_view)
    main_view.add_view(TitleModuleEnum.E_FAQ, faq_view)
    main_view.add_view(TitleModuleEnum.E_OPTIONS, config_view)
    main_view.add_view(TitleModuleEnum.E_DEBUG, debug_view)
    main_view.add_view(TitleModuleEnum.E_DISCOVER, discover_view)

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
