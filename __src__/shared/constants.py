
## ----------------------------------------------
## Configuration application
## ----------------------------------------------

class CTK_APP:
    # Fichier de configuration JSON utilisé pour stocker les paramètres de l'application
    ASPIRABOT_CONFIG_FILE = "config-aspirabot.json"

    # Version de l'application
    VERSION = "1.0.0"

## ----------------------------------------------
## Logger
## ----------------------------------------------

class CTK_LOGGING:
    # Nom de base pour les fichiers de log (sans extension ni timestamp)
    BASE_NAME_LOGFILE = "aspirabot"

    # Dossier pour les fichiers de logs
    DEFAULT_FOLDER_LOGS = "./tmp_logs"

    # Format de logs (ex: 2024-06-01 12:00:00,000 || INFO || app.module || Message de log)
    FORMAT_MSG = '%(asctime)s || %(levelname)s || %(name)s || %(message)s'

    # Taille maximale d'un fichier de log avant rotation (10 MB). Tips -> 1024 * 1024 = 1 MB
    LOG_MAX_BYTES = 10 * 1024 * 1024

    # Nombre de fichiers de log à conserver (ex: app.log.1, app.log.2, etc.)
    BACKUP_LOG_COUNT = 5

## ----------------------------------------------
## Configuration pour le moteur de scraping (Playwright)
## ----------------------------------------------

class CTK_BROWSER:
    # Dossier local pour sauvegarder la session, cookies et cache de Chromium (Playwright)
    DEFAULT_USER_DATA_DIR = "./tmp_chromium_session"

## ----------------------------------------------
## Interface graphique (GUI)
## ----------------------------------------------

class CTK_GUI:
    # Titre de la fenêtre principale
    APP_NAME = "Aspirabot"

    # Dimensions initiales de la fenêtre principale
    DEFAULT_SIZE_ROOT_FRAME = "900x600"

## END
