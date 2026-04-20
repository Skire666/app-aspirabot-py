"""Module de gestion du dépôt des fournisseurs (providers).

Ce module fournit la classe `ProvidersRepository` qui permet de lire,
sauvegarder et gérer les fichiers de configuration des fournisseurs au format JSON.
"""

import logging
import json
from pathlib import Path
from typing import Any, List
from models.provider_model import ProviderModel

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersRepository:
    """Gère l'accès aux données des fournisseurs stockées sur le système de fichiers.

    Cette classe agit comme un dépôt (repository) de données pour les objets de type
    `ProviderModel`, en facilitant leur lecture globale, la détermination
    de nouveaux chemins de fichiers, et la sauvegarde de leurs données de configuration.

    Attributes:
        folder_path (str | Path): Le chemin vers le dossier contenant les fichiers JSON des fournisseurs.
    """

    def __init__(self, path_folder: str | Path) -> None:
        """Initialise le dépôt des fournisseurs.

        Args:
            path_folder (str | Path): Le chemin vers le dossier contenant les fichiers JSON des fournisseurs.

        Example:
            >>> repo = ProvidersRepository("/path/to/providers")
        """
        self._folder_path = path_folder

    def provider_folder_exists(self) -> bool:
        """Vérifie si le dossier contenant les fournisseurs existe sur le système.
        
        Returns:
            bool: True si le dossier existe, False sinon.
        """
        providers_dir = Path(self._folder_path)
        return providers_dir.exists() and providers_dir.is_dir()

    def list_provider_files(self) -> List[Path]:
        """Liste tous les fichiers JSON présents dans le dossier des fournisseurs.

        Returns:
            List[Path]: Une liste de chemins vers les fichiers de fournisseurs.
        """
        providers_dir = Path(self._folder_path)
        if providers_dir.exists() and providers_dir.is_dir():
            return list(providers_dir.glob("*.json"))
        return []

    def read_provider_content_selected(self, name_provider: str) -> ProviderModel:
        """Lit et instancie le fichier de fournisseur spécifié.

        Args:
            name_provider (str): Le nom du fournisseur à lire.

        Returns:
            ProviderModel: L'instance du fournisseur lu.
        """
        for file_path in self.list_provider_files():
            ## On compare le nom du fichier (sans extension) avec le nom du provider recherché
            if file_path.stem == name_provider:
                try:
                    return ProviderModel(str(file_path))
                except Exception as e:
                    s_logger.warning(f"Impossible de lire le provider {file_path}: {e}")
        raise FileNotFoundError(f"Fournisseur non trouvé: {name_provider}")

    def get_next_available_path(self, base_name: str) -> Path:
        """Trouve le prochain nom de fichier disponible avec un suffixe incrémenté.

        Si le fichier cible (ex: `base_name.json`) existe déjà, cette méthode ajoute
        et incrémente un suffixe numérique (ex: `base_name_1.json`, `base_name_2.json`)
        jusqu'à ce qu'un nom de fichier libre soit trouvé.

        Args:
            base_name (str): Le nom de base souhaité pour le fichier (sans l'extension).

        Returns:
            Path: Le chemin complet vers le nouveau fichier qui est disponible pour écriture.

        Example:
            >>> repo = ProvidersRepository("/path/to/providers")
            >>> path = repo.get_next_available_path("nouveau_provider")
            >>> print(path.name)
            'nouveau_provider.json'
        """
        providers_dir = Path(self._folder_path)
        providers_dir.mkdir(parents=True, exist_ok=True)
        
        new_file = providers_dir / f"{base_name}.json"
        counter = 1
        
        # Tant que le fichier existe, incrémente le suffixe pour trouver un nom disponible
        while new_file.exists():
            # Exemple: "folder/base_name_1.json", "folder/base_name_2.json", etc.
            new_file = providers_dir / f"{base_name}_{counter}.json"
            counter += 1
        return new_file

    def save_provider(self, file_path: Path, data: dict[str, Any]) -> None:
        """Sauvegarde les données d'un fournisseur dans un fichier au format JSON.

        Args:
            file_path (Path): Le chemin complet de destination pour enregistrer le fichier.
            data (dict[str, Any]): Le dictionnaire de données représentant les configurations du
                fournisseur à enregistrer.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

