"""Point d'entrée principal de l'application."""

import os
import tkinter as tk
from shared.constants import CTK_GUI
from views.log_view import LogView
from views.config_view import ConfigView
from views.provider_view import ProviderView
from views.main_view import MainView
from views.provider_edit_view import ProviderEditView
from repositories.log_repository import LogRepository
from repositories.json_config_repository import JsonConfigRepository
from repositories.providers_repository import ProvidersRepository
from services.logging_service import LoggingService
from services.config_service import ConfigService
from services.provider_service import ProviderService
from presenters.log_presenter import LogPresenter
from presenters.config_presenter import ConfigPresenter
from presenters.provider_presenter import ProviderPresenter
from presenters.provider_edit_presenter import ProviderEditPresenter

def main() -> None:
    """Initialise les composants principaux et démarre l'application."""

    # Point d'entrée principal de l'application
    app = tk.Tk()
    app.title("Aspirabot")
    app.geometry(CTK_GUI.DEFAULT_SIZE_ROOT_FRAME)
    root_container = tk.Frame(app)
    root_container.pack(fill=tk.BOTH, expand=True)

    # Créer la vue principale avec les onglets verticaux
    main_view = MainView(root_container)
    main_view.pack(fill=tk.BOTH, expand=True)

    # Read configuration
    # Resolving path based on the structure (JSON at the root of the workspace)
    config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config-aspirabot.json")
    config_repo = JsonConfigRepository(config_file_path)
    config_repo.ensure_file_exists()  # Ensure the config file exists before reading
    config_model = config_repo.read_config()

    # Create Logging Component
    if not os.path.exists(config_model.folder_logs):
        os.makedirs(config_model.folder_logs)
    log_file_path = os.path.join(str(config_model.folder_logs), "Aspirabot.log")
    
    logging_service = LoggingService(log_file_path, config_model.log_level)
    log_repository = LogRepository()
    log_view = LogView(main_view.content_area)
    _log_presenter = LogPresenter(view=log_view, service=logging_service, repository=log_repository)

    # Create Configuration Component
    config_service = ConfigService(config_repo)
    config_view = ConfigView(main_view.content_area)
    _config_presenter = ConfigPresenter(view=config_view, service=config_service)

    # Create Provider Component
    provider_repo = ProvidersRepository(config_model.folder_providers, config_model.folder_brokens)
    provider_service = ProviderService(provider_repo)
    provider_view = ProviderView(main_view.content_area)
    provider_presenter = ProviderPresenter(view=provider_view, service=provider_service)

    provider_edit_view = ProviderEditView(main_view.content_area)
    provider_edit_presenter = ProviderEditPresenter(view=provider_edit_view, service=provider_service)

    # Wire events for transition between view providers and edit providers
    def on_request_create_provider():
        provider_edit_presenter.create_new()
        main_view.set_tab_state("Modification", tk.NORMAL)
        main_view.show_view("Modification")

    def on_request_edit_provider(provider_guid: str):
        provider_edit_presenter.load_provider(provider_guid)
        main_view.set_tab_state("Modification", tk.NORMAL)
        main_view.show_view("Modification")

    def on_edit_done():
        provider_presenter.refresh()
        main_view.set_tab_state("Modification", tk.DISABLED)
        main_view.show_view("Fournisseurs")

    provider_presenter.on_request_create_provider = on_request_create_provider
    provider_presenter.on_request_edit_provider = on_request_edit_provider
    provider_edit_presenter.set_on_done_callback(on_edit_done)

    # Register Views to MainView
    main_view.add_view("Journal", log_view)
    main_view.add_view("Configuration", config_view)
    main_view.add_view("Fournisseurs", provider_view)
    main_view.add_view("Modification", provider_edit_view)

    # Default View on startup
    main_view.show_view("Fournisseurs")
    
    app.mainloop()

if __name__ == "__main__":
    main()
