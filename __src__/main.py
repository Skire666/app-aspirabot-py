"""Application entry point for Aspirabot."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk

# Bootstrap: import all step packages to populate the central registry.
import models.steps  # noqa: F401
import services.steps  # noqa: F401
import views.steps  # noqa: F401
from models.app_configuration_model import AppConfigurationModel
from presenters.app_configuration_presenter import AppConfigurationPresenter
from presenters.log_presenter import LogPresenter
from presenters.provider_edit_presenter import ProviderEditPresenter
from presenters.provider_presenter import ProviderPresenter
from presenters.scraping_presenter import ScrapingPresenter
from presenters.splashscreen_presenter import SplashscreenPresenter
from repositories.app_configuration_repository import AppConfigurationRepository
from repositories.log_repository import LogRepository
from repositories.providers_repository import ProvidersRepository
from services.app_configuration_service import ConfigService
from services.logging_service import LoggingService
from services.provider_service import ProviderService
from services.scraping_service import ScrapingService
from services.startup_service import StartupService
from services.web_browser_service import BrowserService
from shared.constants import (
    C_APP_CONFIG_FILE,
    C_BROWSER_ENGINE_PLAYWRIGHT,
)
from shared.i18n_fra import (
    C_TITLE_MODULE_CONFIG,
    C_TITLE_MODULE_FAQ,
    C_TITLE_MODULE_LOGS,
    C_TITLE_MODULE_PROVIDER,
    C_TITLE_MODULE_SCRAPING,
    C_TITLE_MODULE_WORKFLOW,
)
from shared.path_util import get_current_working_directory
from views.app_configuration_view import AppConfigurationView
from views.faq_view import FaqView
from views.log_view import LogView
from views.main_view import MainView
from views.provider_edit_view import ProviderEditView
from views.providers_list_view import ProvidersListView
from views.scraping_panel_view import ScrapingPanelView
from views.splashscreen_view import SplashscreenView

## ---------------------------------------------------------------------------
## Entry point
## ---------------------------------------------------------------------------


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


## ---------------------------------------------------------------------------
## Main application wiring
## ---------------------------------------------------------------------------


def _override_gui_and_style(root: tk.Tk, config_model: AppConfigurationModel) -> None:

    root.title("Aspirabot")
    root.geometry(config_model.gui_booting_size)

    # Maximize the window on launch based on the platform.
    # May be cannot work depending on the window manager
    # but is a best effort to start in a maximized state.
    if config_model.gui_booting_fullscreen:
        if sys.platform.startswith("win"):
            root.state("zoomed")
        elif sys.platform == "darwin":  # macOS
            root.attributes("-zoomed", True)
        else:  # Linux (fallback)
            root.attributes("-zoomed", True)

    # Override global de tous les ttk.Button
    style = ttk.Style()

    style.configure(
        "TButton",
        padding=(6, 6),  # (horizontal, vertical)
    )


def _launch_main_app(
    root: tk.Tk,
    config_repo: AppConfigurationRepository,
    startup_service: StartupService,
) -> None:
    """Configure and reveal the main window after startup succeeds.

    Args:
        root: Root Tk window that was hidden during the splash screen.
        config_repo: Repository reused by the configuration component.
        startup_service: Completed service exposing config_model and logging_service.
    """
    config_model = startup_service.config_model
    logging_service = startup_service.logging_service

    # Apply window settings from the loaded configuration.
    _override_gui_and_style(root, config_model)

    # Build the main sidebar-and-content-area layout.
    root_container = tk.Frame(root)
    root_container.pack(fill=tk.BOTH, expand=True)
    main_view = MainView(root_container)
    main_view.pack(fill=tk.BOTH, expand=True)

    # Instantiate all MVP component groups.
    log_view, log_presenter = _init_log_component(main_view, logging_service)
    config_view, config_presenter = _init_config_component(main_view, config_repo)
    provider_view, provider_presenter, provider_edit_view, provider_edit_presenter, provider_service = (
        _init_provider_components(main_view, config_model)
    )
    scraping_view, scraping_presenter = _init_scraping_component(main_view, config_model, provider_service)
    faq_view = FaqView(main_view.content_area)

    # Wire inter-component navigation and launch callbacks.
    _wire_provider_navigation(main_view, provider_presenter, provider_edit_presenter)
    _wire_scraping_launch(main_view, provider_presenter, provider_service, scraping_presenter)
    _wire_workflow_guard(main_view, provider_presenter, scraping_presenter)

    # Register views, reveal the window, and anchor presenters against GC.
    _register_views(main_view, log_view, config_view, provider_view, provider_edit_view, scraping_view, faq_view)
    root._app_presenters = [  # type: ignore[attr-defined]
        log_presenter,
        config_presenter,
        provider_presenter,
        provider_edit_presenter,
        scraping_presenter,
    ]
    root.deiconify()


## ---------------------------------------------------------------------------
## Component factories
## ---------------------------------------------------------------------------


def _init_log_component(
    main_view: MainView,
    logging_service: LoggingService,
) -> tuple[LogView, LogPresenter]:
    """Create and wire the journal (log display) component.

    Args:
        main_view: Main container providing the content area as parent.
        logging_service: Service that broadcasts log events to the presenter.

    Returns:
        A (LogView, LogPresenter) tuple.
    """
    log_repository = LogRepository()
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


def _init_provider_components(
    main_view: MainView,
    config_model: AppConfigurationModel,
) -> tuple[
    ProvidersListView,
    ProviderPresenter,
    ProviderEditView,
    ProviderEditPresenter,
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
    provider_view = ProvidersListView(main_view.content_area)
    provider_presenter = ProviderPresenter(view=provider_view, service=provider_service)

    # Provider edit view and presenter.
    provider_edit_view = ProviderEditView(main_view.content_area)
    provider_edit_presenter = ProviderEditPresenter(view=provider_edit_view, provider_service=provider_service)

    return provider_view, provider_presenter, provider_edit_view, provider_edit_presenter, provider_service


def _init_scraping_component(
    main_view: MainView,
    config_model: AppConfigurationModel,
    provider_service: ProviderService,
) -> tuple[ScrapingPanelView, ScrapingPresenter]:
    """Create and wire the scraping panel component.

    Args:
        main_view: Main container providing the content area as parent.
        config_model: Configuration model supplying the scraping output folder.
        provider_service: The provider service for managing provider data.

    Returns:
        A (ScrapingPanelView, ScrapingPresenter) tuple.
    """
    if config_model.browser_engine == C_BROWSER_ENGINE_PLAYWRIGHT:
        browser_service = BrowserService(config_model.folder_scraping)
    else:
        raise Exception(f"Unsupported browser engine: {config_model.browser_engine}")
    scraping_service = ScrapingService(config_model.folder_scraping, browser_service)
    scraping_view = ScrapingPanelView(main_view.content_area)
    scraping_presenter = ScrapingPresenter(
        view=scraping_view, service_scraping=scraping_service, service_provider=provider_service
    )
    return scraping_view, scraping_presenter


## ---------------------------------------------------------------------------
## Navigation wiring
## ---------------------------------------------------------------------------


def _wire_provider_navigation(
    main_view: MainView,
    provider_presenter: ProviderPresenter,
    provider_edit_presenter: ProviderEditPresenter,
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
        main_view.set_tab_state(C_TITLE_MODULE_WORKFLOW, tk.NORMAL)
        main_view.show_view(C_TITLE_MODULE_WORKFLOW)

    def on_request_edit_provider(id_file: str) -> None:
        # Load the selected provider into the edit form and navigate to it.
        provider_edit_presenter.load_provider(id_file)
        main_view.set_tab_state(C_TITLE_MODULE_WORKFLOW, tk.NORMAL)
        main_view.show_view(C_TITLE_MODULE_WORKFLOW)

    def on_edit_done() -> None:
        # Return to the list and disable the edit tab after save/cancel.
        provider_presenter.refresh()
        main_view.set_tab_state(C_TITLE_MODULE_WORKFLOW, tk.DISABLED)
        main_view.show_view(C_TITLE_MODULE_PROVIDER)

    # Inject all navigation callbacks into the two presenters.
    provider_presenter.on_request_create_provider = on_request_create_provider
    provider_presenter.on_request_edit_provider = on_request_edit_provider
    provider_edit_presenter.set_on_done_callback(on_edit_done)


def _wire_scraping_launch(
    main_view: MainView,
    provider_presenter: ProviderPresenter,
    provider_service: ProviderService,
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
        print(f"Request to launch provider with id_file={id_file}")
        scraping_presenter.load_provider(id_file)
        main_view.set_tab_state(C_TITLE_MODULE_SCRAPING, tk.NORMAL)
        main_view.show_view(C_TITLE_MODULE_SCRAPING)

    provider_presenter.on_request_launch_provider = on_request_launch_provider


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
        return main_view.get_tab_state(C_TITLE_MODULE_WORKFLOW) == tk.NORMAL

    # Inject into both presenters so either can check the guard independently.
    provider_presenter.is_workflow_active = is_workflow_active
    scraping_presenter.is_workflow_active = is_workflow_active


## ---------------------------------------------------------------------------
## View registration
## ---------------------------------------------------------------------------


def _register_views(
    main_view: MainView,
    log_view: LogView,
    config_view: AppConfigurationView,
    provider_view: ProvidersListView,
    provider_edit_view: ProviderEditView,
    scraping_view: ScrapingPanelView,
    faq_view: FaqView,
) -> None:
    """Register all module views with the sidebar and display the default tab.

    Args:
        main_view: Navigation shell that controls which view is visible.
        log_view: Journal module view.
        config_view: Configuration module view.
        provider_view: Providers list module view.
        provider_edit_view: Provider edit module view.
        scraping_view: Scraping panel module view.
        faq_view: FAQ module view.
    """
    # Map each sidebar label to its corresponding view widget.
    main_view.add_view(C_TITLE_MODULE_LOGS, log_view)
    main_view.add_view(C_TITLE_MODULE_PROVIDER, provider_view)
    main_view.add_view(C_TITLE_MODULE_WORKFLOW, provider_edit_view)
    main_view.add_view(C_TITLE_MODULE_SCRAPING, scraping_view)
    main_view.add_view(C_TITLE_MODULE_FAQ, faq_view)
    main_view.add_view(C_TITLE_MODULE_CONFIG, config_view)

    # Land on the providers list as the startup default.
    main_view.show_view(C_TITLE_MODULE_PROVIDER)


## ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()

## END
