import logging
import os
import queue
from logging.handlers import RotatingFileHandler
from typing import Optional

from shared.constants import CTK_LOGGING
from shared.string_helper import StringHelper

class QueueLogHandler(logging.Handler):
    """
    Handler de logging personnalisé qui envoie les enregistrements de logs (LogRecord)
    dans une file d'attente (Queue) thread-safe.
    
    Cela permet à l'interface Tkinter de lire ces logs de façon asynchrone sans
    couplage fort ni blocage de l'interface principale.
    """
    def __init__(self, log_queue: queue.Queue[tuple[logging.LogRecord, str]]) -> None:
        """
        Initialise le handler avec la file d'attente spécifiée.

        Args:
            log_queue (queue.Queue): La file d'attente thread-safe pour stocker les LogRecord.
        """
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        """
        Intercepte un enregistrement de log et le place dans la file d'attente.

        Args:
            record (logging.LogRecord): L'enregistrement de log intercepté par le handler.
        """
        try:
            msg = self.format(record)
            self.log_queue.put((record, msg))
        except Exception:
            self.handleError(record)


def setup_logger(log_queue: Optional[queue.Queue[tuple[logging.LogRecord, str]]] = None, name: str = "", level: str = "INFO") -> logging.Logger:
    """
    Configure le système de logging avec rotation de fichier, sortie console,
    et optionnellement un QueueHandler pour l'interface graphique.

    Évite la duplication des handlers si appelé plusieurs fois.
    Le niveau de log est lu depuis la variable d'environnement LOG_LEVEL (INFO par défaut).

    Args:
        log_queue (Optional[queue.Queue], optional): File d'attente pour le handler Tkinter. 
            Défaut à None.
        name (str, optional): Nom du logger root ou spécifique.
        level (str, optional): Niveau de logging. Par défaut "INFO".

    Returns:
        logging.Logger: Le logger racine configuré.
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
    """
    Met à jour dynamiquement le niveau de log d'un logger et de tous ses handlers.
    Sauvegarde également ce niveau dans l'environnement pour les futurs loggers.

    Args:
        logger (logging.Logger): Le logger à mettre à jour.
        new_level_str (str): Le nouveau niveau de log sous forme de chaîne (ex: "DEBUG").
    """
    level = new_level_str.upper()
    # Sauvegarde pour les futurs appels à setup_logger
    os.environ["LOG_LEVEL"] = level
    
    level_val = getattr(logging, level, logging.INFO)
    logger.setLevel(level_val)
    for handler in logger.handlers:
        handler.setLevel(level_val)

## END
