"""Module utilitaire pour la journalisation.

Ce module fournit des outils pour configurer les logs et gérer 
des handlers personnalisés, comme le `QueueLogHandler` qui s'interface
idéalement avec Tkinter pour un affichage asynchrone des logs.
"""

import logging
import os
import queue
from logging.handlers import RotatingFileHandler
from typing import Optional, Tuple

from shared.constants import CTK_LOGGING
from shared.string_helper import StringHelper

class QueueLogHandler(logging.Handler):
    """Handler de logging personnalisé utilisant une file d'attente (Queue).

    Ce handler intercepte les enregistrements de logs (LogRecord) et les stocke
    dans une file d'attente thread-safe `queue.Queue`. Cela permet à l'interface
    Tkinter de lire ces logs de façon asynchrone sans risquer un blocage du thread
    principal de l'UI (le GUI thread).

    Attributes:
        log_queue (queue.Queue): File d'attente stockant un tuple comprenant le `LogRecord`
            et son message formaté en chaîne `str`.
    """
    def __init__(self, log_queue: queue.Queue[Tuple[logging.LogRecord, str]]) -> None:
        """Initialise le QueueLogHandler.

        Args:
            log_queue (queue.Queue[Tuple[logging.LogRecord, str]]): La file
                d'attente thread-safe où insérer les logs.

        Exemples d'utilisation:
            >>> file_attente = queue.Queue()
            >>> handler = QueueLogHandler(file_attente)
            >>> logging.getLogger().addHandler(handler)
        """
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        """Intercepte un enregistrement de log et le place dans la file.

        Args:
            record (logging.LogRecord): L'enregistrement de log émis.

        Raises:
            Exception: S'il est impossible de traiter ou formater le `record`,
                l'exception est capturée et transférée via `handleError`.
        """
        try:
            msg = self.format(record)
            self.log_queue.put((record, msg))
        except Exception:
            self.handleError(record)


def setup_logger(log_queue: Optional[queue.Queue[Tuple[logging.LogRecord, str]]] = None, name: str = "", level: str = "INFO") -> logging.Logger:
    """Configure le système de journalisation (logging).
    
    Il paramètre la sortie sur la console, la sortie vers un fichier via un
    `RotatingFileHandler`, et de manière optionnelle un envoi asynchrone 
    vers un `QueueLogHandler` si la `log_queue` est fournie. Ce logger empêche
    la duplication des handlers lors des appels multiples.
    Le niveau de log peut également être défini par une variable d'environnement `LOG_LEVEL`.

    Args:
        log_queue (Optional[queue.Queue[Tuple[logging.LogRecord, str]]], optional): 
            File d'attente pour intercepter les logs (utile pour UI Tkinter). Par défaut None.
        name (str, optional): Nom du système Logger (par défaut le root logger).
        level (str, optional): Le niveau initial ("DEBUG", "INFO", "WARNING", etc.). Par défaut "INFO".

    Returns:
        logging.Logger: Le logger configuré et prêt à l'emploi.

    Exemples d'utilisation:
        >>> logger = setup_logger(name="MonApp", level="DEBUG")
        >>> logger.debug("Message debug")
    """
    # Lit le niveau depuis l'environnement ou utilise le paramètre
    log_level_str = os.environ.get("LOG_LEVEL", level).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger(name if name else None)
    
    # Si des handlers existent déjà, on évite d'en rajouter des multiples
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    # Format principal : Date Heure - Niveau - Nom - Message
    formatter = logging.Formatter(CTK_LOGGING.FORMAT_MSG)

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler
    log_dir = CTK_LOGGING.DEFAULT_FOLDER_LOGS
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, StringHelper.concat_yyyy_and_extension(CTK_LOGGING.BASE_NAME_LOGFILE, "log")),
        maxBytes= CTK_LOGGING.LOG_MAX_BYTES,
        backupCount= CTK_LOGGING.BACKUP_LOG_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. Queue Handler pour l'UI MVC (si fournie)
    if log_queue is not None:
        queue_handler = QueueLogHandler(log_queue)
        queue_handler.setLevel(log_level)
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

    return logger

def update_logger_level(logger: logging.Logger, new_level_str: str) -> None:
    """Met à jour dynamiquement le niveau de sévérité d'un logger.

    Non seulement le niveau principal est ajusté, mais tous les handlers attachés
    prennent également ce niveau (par exemple la Console et le fichier log).
    La nouvelle métrique est également définie dans la variable d'environnement `LOG_LEVEL`.

    Args:
        logger (logging.Logger): Le logger dont la sévérité doit être affectée.
        new_level_str (str): Le format texte du niveau (ex: "DEBUG", "ERROR").

    Raises:
        AttributeError: Si la chaîne `new_level_str` ne correspond pas à un niveau existant dans logging,
            le niveau de repli sera appliqué logiquement `logging.INFO`. (Comportement Python interne)

    Exemples d'utilisation:
        >>> logger = logging.getLogger("MonApp")
        >>> update_logger_level(logger, "DEBUG")
    """
    level = new_level_str.upper()
    # Sauvegarde pour les futurs appels à setup_logger
    os.environ["LOG_LEVEL"] = level
    
    level_val = getattr(logging, level, logging.INFO)
    logger.setLevel(level_val)
    for handler in logger.handlers:
        handler.setLevel(level_val)

## END
