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
    """Gère l'accès aux opérations du système de fichiers."""

    @staticmethod
    def open_folder(folder_path: str | Path) -> None:
        """Ouvre un dossier dans l'explorateur de fichiers de l'OS.
        
        Args:
            folder_path (str | Path): Le chemin vers le dossier à ouvrir.
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
