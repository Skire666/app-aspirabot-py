"""Module de gestion du dépôt des fournisseurs de scraping.

Ce module fournit la classe `ProvidersRepository` qui permet de découvrir, lire,
charger et supprimer les fichiers de configuration de fournisseurs (sous format JSON)
présents dans un répertoire local cible.

Exemples d'utilisation:
    >>> from repositories.providers_repository import ProvidersRepository
    >>> repo = ProvidersRepository("./providers")
    >>> liste_fichiers = repo.list_provider_files()
"""

import logging
import os
from pathlib import Path
from typing import List, Union
from repositories.file_manager_repository import FileManagerRepository
from models.provider_model import ProviderModel

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersRepository:
    """Gère l'accès aux données des fournisseurs stockées sur le système de fichiers.

    Cette classe agit comme un dépôt de données pour la collection locale de configurations.
    Elle encapsule les opérations de listage de répertoire, instanciation asynchrone
    du modèle `ProviderModel`, navigation Windows/Linux, et suppression logique du disque.

    Attributes:
        _folder_path (Path): Le chemin formaté pointant vers le dossier contenant les JSON.
        logger (logging.Logger): Le journaliseur interne défini pour tracer les exécutions.
    """

    def __init__(self, path_folder: Union[str, Path]) -> None:
        """Initialise le dépôt en pointant vers un dossier local contenant les fournisseurs.

        Args:
            path_folder (Union[str, Path]): Le chemin vers le dossier où chercher les fichiers JSON.

        Exemples d'utilisation:
            >>> repo = ProvidersRepository("/chemin/vers/providers")
        """
        self._folder_path: Path = Path(path_folder)
        self.logger = logging.getLogger(__name__)

    @property
    def folder_path(self) -> Path:
        """Path: Obtient ou définit le chemin dynamique utilisé pour cibler le dossier des JSON."""
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value: Union[str, Path]) -> None:
        self._folder_path = Path(value)

    def list_provider_files(self) -> List[Path]:
        """Examine le dossier sélectionné et retourne tous les fichiers .json présents.

        Vérifie l'existence du chemin spécifié et parcourt son contenu pour retenir 
        exclusivement ceux avec l'extension `.json`.

        Returns:
            List[Path]: Une liste de chemins (`pathlib.Path`) correspondant aux fichiers trouvés.
                Retourne une liste vide `[]` si le dossier est invalide ou vide.
                
        Exemples d'utilisation:
            >>> chemins = repo.list_provider_files()
            >>> print(chemins)
            [WindowsPath('./providers/base1.json'), WindowsPath('./providers/base2.json')]
        """
        if self._folder_path.exists() and self._folder_path.is_dir():
            return list(self._folder_path.glob("*.json"))
        return []

    def read_provider_content_selected(self, name_provider: str) -> ProviderModel:
        """Charge un fichier fournisseur par son nom et l'instancie sous forme de modèle.

        Recherche parmi l'ensemble des fichiers disponibles celui qui correspond au
        nom complet (avec extension) ou de base (sans extension) fourni en paramètre.

        Args:
            name_provider (str): Le nom du fichier ou sa racine. Exemple: 'fournisseur_1' ou 'fournisseur_1.json'.

        Returns:
            ProviderModel: L'instance instanciée du fichier de configuration choisi.

        Raises:
            FileNotFoundError: Si le fournisseur recherché est introuvable après balayage.
            Exception: Si l'instanciation de `ProviderModel` échoue (capturée, transforme en skip).
            
        Exemples d'utilisation:
            >>> modele = repo.read_provider_content_selected("mon_provider.json")
            >>> print(modele.url)
            'https://example.com'
        """
        for file_path in self.list_provider_files():
            ## On compare le nom du fichier avec le nom du provider recherché
            if file_path.name == name_provider or file_path.stem == name_provider:
                try:
                    return ProviderModel(str(file_path))
                except Exception as e:
                    self.logger.warning(f"Impossible de lire le provider {file_path}: {e}")
                    
        raise FileNotFoundError(f"Fournisseur non trouvé: {name_provider}")

    def open_providers_folder(self) -> None:
        """Déclenche l'affichage du dossier des fournisseurs dans l'explorateur système.
        
        Permet à l'utilisateur de consulter ou d'éditer manuellement les fichiers JSON locaux.
        Utilise en interne la fonction statique d'aide OS (`FileManagerRepository.open_folder`).
        
        Returns:
            None
        """
        self.logger.info("Ouverture du dossier des fournisseurs...")
        if not self._folder_path.exists():
            os.makedirs(self._folder_path)
        if not self._folder_path.is_dir():
            raise NotADirectoryError(f"Le chemin spécifié n'est pas un dossier: {self._folder_path}")
        FileManagerRepository.open_folder(self.folder_path)

    def delete_provider(self, provider_filename: str) -> None:
        """Supprime définitivement un fournisseur de configuration du système de fichiers.

        Args:
            provider_filename (str): Le nom du fichier avec extension à supprimer (ex: "prov.json").

        Returns:
            None
            
        Raises:
            OSError: En cas de droits insuffisants ou si le fichier est verrouillé par un processus.
            FileNotFoundError: Si le fichier cible est déjà absent (via os.remove interne).
        """
        provider_path = self._folder_path / provider_filename
        self.logger.info(f"Suppression du fournisseur: {provider_path}")
        os.remove(provider_path)
