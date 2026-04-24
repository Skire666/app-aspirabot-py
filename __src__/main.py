"""Point d'entrée principal de l'application Scraper Configurator.

Ce module contient la fonction principale qui sert de point d'entrée pour l'application.
Il est responsable de l'initialisation du gestionnaire de logs, du chargement de la 
configuration, et du lancement de l'interface graphique Tkinter.

Exemples:
    Pour lancer l'application, exécutez ce script depuis le terminal racine :
        $ python __src__/main.py
"""

from shared.constants import CTK_APP
from views.root_frame_view import RootFrameView
from utils.logging_util import setup_logger, update_logger_level

# Repositories & Services import
from repositories.json_config_repository import JsonConfigRepository
from repositories.providers_repository import ProvidersRepository
from services.config_service import ConfigService
from services.provider_service import ProviderService

# Controllers import
from controllers.providers_list_controller import ProvidersListController
from controllers.update_controller import UpdateController
from controllers.scraping_controller import ScrapingController
from controllers.config_controller import ConfigController

def main() -> None:
    """Initialise les composants principaux et démarre l'application.

    Cette fonction configure le logger initial, charge la configuration de 
    l'application depuis le fichier de configuration défini, met à jour 
    le niveau de log en fonction des préférences de l'utilisateur, 
    et démarre la boucle principale de l'interface graphique (Tkinter).

    Args:
        None

    Returns:
        None

    Raises:
        FileNotFoundError: Si le fichier de configuration est introuvable (géré par le modèle).
        KeyError: Si une clé de configuration essentielle est manquante.

    Exemple d'utilisation:
        >>> main()
    """
    # Initialisation du Logger principal au démarrage avec un niveau par défaut (DEBUG)
    logger = setup_logger(name="app", level="DEBUG")
    logger.info(" ---------------- Démarrage de l'application ----------------")

    # Chargement de la configuration
    logger.info("Chargement des configurations.")
    
    # Configuration Repository & Service Setup
    config_repository = JsonConfigRepository(CTK_APP.ASPIRABOT_CONFIG_FILE)
    config_service = ConfigService(config_repository)

    # Récupération et vérification de la configuration
    config = config_service.get_config()
    config_service.verify_configuration()
    logger.debug("Configuration chargée et validée.")
    
    # Mise à jour dynamique du niveau de log selon la configuration
    log_level_str = config.log_level
    update_logger_level(logger, log_level_str)

    logger.debug("Chargement des configurations et initialisation terminés.")
    
    # Providers Repository & Service Setup
    providers_repository = ProvidersRepository(config.folder_providers)
    provider_service = ProviderService(providers_repository)
    
    # Controllers setup
    providers_list_controller = ProvidersListController(provider_service, config)
    update_controller = UpdateController(provider_service, config)
    scraping_controller = ScrapingController(provider_service, config)
    config_controller = ConfigController(config_service)

    # Point d'entrée principal de l'application
    app = RootFrameView(
        providers_list_controller, 
        update_controller, 
        scraping_controller, 
        config_controller
    )
    app.mainloop()

if __name__ == "__main__":
    main()
