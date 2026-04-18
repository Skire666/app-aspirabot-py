"""
Point d'entrée principal de l'application Scraper Configurator.
Initialise le gestionnaire de logs, la configuration et lance l'interface graphique.
"""

from constants import CTK_APP
from views.root_frame_view import RootFrameView
from models.aspirabot_app_model import AspirabotAppModel
from utils.logging_util import setup_logger, update_logger_level

def main() -> None:
    """
    Initialise les composants principaux et démarre la boucle Tkinter.
    """
    # Initialisation du Logger principal au démarrage avec un niveau par défaut (INFO)
    logger = setup_logger(name="app", level="DEBUG")
    logger.info(" ---------------- Démarrage de l'application ----------------")

    # Chargement de la configuration
    logger.info("Chargement des configurations.")
    config = AspirabotAppModel(CTK_APP.ASPIRABOT_CONFIG_FILE)
    config.verify_keys_exist()  # Vérifie que toutes les clés par défaut sont présentes.
    logger.debug("Configuration chargée.")
    
    # Mise à jour dynamique du niveau de log selon la configuration
    log_level_str = config.log_level
    update_logger_level(logger, log_level_str)

    logger.debug("Chargement des configurations et initialisation terminés.")
    
    # Point d'entrée principal de l'application
    app = RootFrameView(app_config=config)
    app.mainloop()

if __name__ == "__main__":
    main()
