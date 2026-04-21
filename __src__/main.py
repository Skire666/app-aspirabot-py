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
from models.config_aspirabot_model import ConfigAspirabotModel
from utils.logging_util import setup_logger, update_logger_level

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
    config = ConfigAspirabotModel(CTK_APP.ASPIRABOT_CONFIG_FILE)
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
