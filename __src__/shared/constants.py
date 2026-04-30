"""Constantes globales pour l'application Aspirabot.

Ce module regroupe l'ensemble des constantes de configuration,
des paramètres de logs, de l'interface graphique et du navigateur.
Il permet de centraliser les valeurs statiques pour faciliter leur
modification et garantir la cohérence dans tout le projet.

Exemples d'utilisation:
    >>> from shared.constants import CTK_APP, CTK_LOGGING
    >>> print(CTK_APP.VERSION)
    '1.0.0'
"""

import os

# Racine du projet : __src__/shared/constants.py → shared/ → __src__/ → racine
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

## ----------------------------------------------
## Configuration application
## ----------------------------------------------


class CTK_APP:
    """Constantes liées à la configuration générale de l'application.

    Attributes:
        ASPIRABOT_CONFIG_FILE (str): Fichier de configuration JSON.
        VERSION (str): Version actuelle de l'application.
    """

    ASPIRABOT_CONFIG_FILE: str = "config-aspirabot.json"
    VERSION: str = "1.0.0"


## ----------------------------------------------
## Logger
## ----------------------------------------------


class CTK_LOGGING:
    """Constantes liées à la configuration du système de journalisation (logs).

    Attributes:
        BASE_NAME_LOGFILE (str): Nom de base pour les fichiers de log.
        DEFAULT_FOLDER_LOGS (str): Dossier par défaut pour stocker les logs.
        FORMAT_MSG (str): Format des messages de log.
        LOG_MAX_BYTES (int): Taille maximale d'un fichier de log (en octets) avant rotation.
        BACKUP_LOG_COUNT (int): Nombre de fichiers de log de secours à conserver.
    """

    BASE_NAME_LOGFILE: str = "aspirabot"
    DEFAULT_FOLDER_LOGS: str = os.path.join(_BASE_DIR, "tmp_app_logs")
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    BACKUP_LOG_COUNT: int = 5


class CTK_USER:
    """Constantes liées à la configuration des dossiers de travail pour les données utilisateur."""

    DEFAULT_USER_PROVIDER: str = os.path.join(_BASE_DIR, "tmp_user_providers")
    DEFAULT_USER_BROKENS: str = os.path.join(_BASE_DIR, "tmp_user_brokens")
    DEFAULT_USER_OUTPUT: str = os.path.join(_BASE_DIR, "tmp_user_output")


## ----------------------------------------------
## Configuration pour le moteur de scraping (Playwright)
## ----------------------------------------------


class CTK_BROWSER:
    """Constantes liées à la configuration du navigateur pour le scraping.

    Attributes:
        DEFAULT_FOLDER_TMP_CHROMIUM (str): Dossier local par défaut pour stocker
            les données utilisateurs Chromium (sessions, cookies, cache).
    """

    DEFAULT_FOLDER_TMP_CHROMIUM: str = os.path.join(_BASE_DIR, "tmp_chromium_session")


## ----------------------------------------------
## Interface graphique (GUI)
## ----------------------------------------------


class CTK_GUI:
    """Constantes liées à la configuration de l'interface utilisateur.

    Attributes:
        APP_NAME (str): Titre de la fenêtre principale.
        DEFAULT_SIZE_ROOT_FRAME (str): Dimensions par défaut de la fenêtre principale.
    """

    APP_NAME: str = "Aspirabot"
    DEFAULT_SIZE_ROOT_FRAME: str = "950x600"


## END
