"""Module de gestion des répertoires et fichiers de l'OS.

Ce module fournit la classe `FileManagerRepository` qui abstrait
les interactions avec le système d'exploitation natif pour des actions
telles que l'ouverture de dossiers dans l'explorateur de fichiers local 
de l'utilisateur.

Exemples d'utilisation:
    >>> from repositories.file_manager_repository import FileManagerRepository
    >>> FileManagerRepository.open_folder("./mon_dossier")
"""

import logging
import platform
import os
import subprocess
from pathlib import Path

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Classe
## ----------------------------------------------

class FileManagerRepository:
    """Gère l'accès aux opérations du système de fichiers natif.
    
    Cette classe regroupe des méthodes statiques facilitant les interactions
    entre l'application et l'OS hôte, indépendamment de la plateforme
    (Windows, macOS, Linux).
    """

    @staticmethod
    def open_folder(folder_path: str | Path) -> None:
        """Ouvre un dossier dans l'explorateur de fichiers par défaut de l'OS.
        
        Vérifie d'abord l'existence du dossier spécifié. Si le dossier existe,
        la méthode invoque la commande système appropriée (`startfile` pour Windows,
        `open` pour macOS, ou `xdg-open` pour Linux) pour afficher le dossier.

        Args:
            folder_path (str | Path): Le chemin (absolu ou relatif) vers le dossier à ouvrir.

        Returns:
            None

        Raises:
            Aucune exception n'est explicitement levée (les erreurs systèmes sont capturées et logguées).

        Exemples d'utilisation:
            >>> FileManagerRepository.open_folder(Path("C:/Utilisateurs/Documents"))
            >>> FileManagerRepository.open_folder("./config_dir")
        """
        path = Path(folder_path).resolve()
        if not path.exists():
            s_logger.warning(f"Le dossier n'existe pas : {path}")
            return
            
        try:
            if platform.system() == "Windows":
                os.startfile(path) # type: ignore
            elif platform.system() == "Darwin": # macOS
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)]) # Linux et autres
            s_logger.info(f"Dossier ouvert : {path}")
        except Exception as e:
            s_logger.error(f"Erreur lors de l'ouverture du dossier : {e}")
