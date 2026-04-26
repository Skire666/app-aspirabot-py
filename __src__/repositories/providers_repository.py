"""Module de gestion du dépôt des fournisseurs de scraping.

Ce module fournit la classe `ProvidersRepository` qui permet de découvrir, lire,
charger et supprimer les fichiers de configuration de fournisseurs (sous format JSON)
présents dans un répertoire local cible.

Exemples d'utilisation:
    >>> from repositories.providers_repository import ProvidersRepository
    >>> repo = ProvidersRepository("./providers")
    >>> liste_providers = repo.list_providers()
"""

from typing import List, Union, Dict, Any, cast
from pathlib import Path
import os
import json
import shutil
import subprocess
import logging
from datetime import datetime
from dataclasses import asdict
from shared.operating_system_util import OperatingSystem, detect_os
from models.provider_model import ProviderModel
from repositories.json_repository import JsonFileRepository
from interfaces.provider_repository_interface import ProviderRepositoryInterface


## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersRepository(ProviderRepositoryInterface):
    """Gère l'accès aux données des fournisseurs stockées sur le système de fichiers.

    Cette classe agit comme un dépôt de données pour la collection locale de configurations.
    Elle encapsule les opérations de listage de répertoire, chargement/sauvegarde des fichiers JSON,
    conversion vers/depuis ProviderModel, navigation Windows/Linux, et suppression du disque.

    Attributes:
        _folder_path (Path): Le chemin formaté pointant vers le dossier contenant les JSON.
        logger (logging.Logger): Le journaliseur interne défini pour tracer les exécutions.
    """

    def __init__(self, folder_providers: Union[str, Path], folder_brokens: Union[str, Path]) -> None:
        """Initialise le dépôt en pointant vers un dossier local contenant les fournisseurs.

        Args:
            folder_providers (Union[str, Path]): Le chemin vers le dossier où chercher les fichiers JSON.
            folder_brokens (Union[str, Path]): Le chemin vers le dossier où stocker les fichiers cassés.

        Exemples d'utilisation:
            >>> repo = ProvidersRepository("/chemin/vers/providers", "/chemin/vers/brokens")
        """
        self._folder_path: Path = Path(folder_providers)
        self._folder_brokens: Path = Path(folder_brokens)
        self.logger = logging.getLogger(__name__)

    @property
    def folder_path(self) -> Path:
        """Path: Obtient le chemin utilisé pour cibler le dossier des JSON."""
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value: Union[str, Path]) -> None:
        """Définit le chemin du dossier des JSON."""
        self._folder_path = Path(value)

    def _list_provider_files(self) -> List[Path]:
        """Examine le dossier sélectionné et retourne tous les fichiers .json présents.

        Vérifie l'existence du chemin spécifié et parcourt son contenu pour retenir 
        exclusivement ceux avec l'extension `.json`.

        Returns:
            List[Path]: Une liste de chemins (`pathlib.Path`) correspondant aux fichiers trouvés.
                Retourne une liste vide `[]` si le dossier est invalide ou vide.
        """
        if self._folder_path.exists() and self._folder_path.is_dir():
            return list(self._folder_path.glob("*.json"))
        return []

    def list_provider_files(self) -> List[Path]:
        """Lists all files in the providers directory.

        Returns:
            The sorted list of files found in the providers folder.
        """
        if not self._folder_path.exists() or not self._folder_path.is_dir():
            return []

        return sorted(
            [path for path in self._folder_path.iterdir() if path.is_file()],
            key=lambda path: path.name.lower(),
        )

    def read_provider_file_data(self, file_path: Path) -> Dict[str, Any]:
        """Reads a provider file and returns the decoded JSON content.

        Args:
            file_path: File to read.

        Returns:
            The decoded JSON payload.

        Raises:
            OSError: When the file cannot be read.
            json.JSONDecodeError: When the content is not valid JSON.
        """
        with file_path.open("r", encoding="utf-8") as file_handle:
            content = json.load(file_handle)

        if not isinstance(content, dict):
            raise ValueError(f"Contenu JSON invalide dans {file_path.name}")

        return cast(Dict[str, Any], content)

    def ensure_broken_folder(self) -> Path:
        """Ensures the broken-folder exists and returns its path."""
        broken_folder = self._folder_brokens
        broken_folder.mkdir(parents=True, exist_ok=True)
        return broken_folder

    def move_invalid_provider_file(self, file_path: Path, reason: str) -> Path:
        """Moves an invalid provider file to the broken folder.

        Args:
            file_path: The invalid file to move.
            reason: The reason for the move, used for logging.

        Returns:
            The destination path of the moved file.
        """
        broken_folder = self.ensure_broken_folder()
        mini_timestamp = datetime.now().strftime("%H%M%S%f")
        destination_name = f"{mini_timestamp}{file_path.suffix}"
        destination_path = broken_folder / destination_name

        self.logger.warning(
            "Déplacement du fichier invalide %s vers %s (%s)",
            file_path,
            destination_path,
            reason,
        )
        shutil.move(str(file_path), str(destination_path))
        return destination_path

    def _dict_to_provider_model(self, data: Dict[str, Any]) -> ProviderModel:
        """Convertit un dictionnaire JSON en instance ProviderModel.

        Filtre les clés du dictionnaire pour ne garder que celles définies dans ProviderModel.

        Args:
            data (Dict[str, Any]): Le dictionnaire contenant les données du fournisseur.

        Returns:
            ProviderModel: L'instance instanciée du modèle.
        """
        # Récupère uniquement les champs présents dans ProviderModel
        provider_fields = {
            'provider_guid',
            'provider_name',
            'url',
            'created_date',
            'modified_date',
            'version',
            'browser_displayed',
            'automation_obfuscated',
            'steps'
        }
        filtered_data = {k: v for k, v in data.items() if k in provider_fields}
        return ProviderModel(**filtered_data)

    def _provider_model_to_dict(self, provider: ProviderModel) -> Dict[str, Any]:
        """Convertit une instance ProviderModel en dictionnaire pour la sérialisation JSON.

        Args:
            provider (ProviderModel): L'instance du modèle à convertir.

        Returns:
            Dict[str, Any]: Le dictionnaire sérialisable en JSON.
        """
        return asdict(provider)
    
    def exists_provider(self, provider_guid: str) -> bool:
        """Vérifie l'existence d'un fournisseur dans le dossier.

        Args:
            provider_guid (str): L'identifiant unique du fournisseur à vérifier.

        Returns:
            bool: `True` si un fichier correspondant existe, sinon `False`.
        """
        full_filepath = self._folder_path / str(provider_guid + ".json")
        return full_filepath.exists() and full_filepath.is_file()

    def read_provider(self, provider_guid: str) -> ProviderModel:
        """Charge un fichier fournisseur par son ID et l'instancie sous forme de modèle.

        Recherche parmi l'ensemble des fichiers disponibles celui qui correspond au
        nom complet (avec extension) ou de base (sans extension) fourni en paramètre.

        Args:
            provider_guid (str): L'identifiant unique du fournisseur à charger.

        Returns:
            ProviderModel: L'instance instanciée du fichier de configuration choisi.

        Raises:
            FileNotFoundError: Si le fournisseur recherché est introuvable après balayage.
            
        Exemples d'utilisation:
            >>> modele = repo.get_provider("mon_provider.json")
            >>> print(modele.url)
            'https://example.com'
        """
        # Construit le chemin complet du fichier
        full_filepath = self._folder_path / str(provider_guid + ".json")

        try:
            if not full_filepath.exists():
                raise FileNotFoundError(f"Fournisseur non trouvé: {provider_guid}")
            
            # Charge le fichier JSON via JsonFileRepository
            json_repo = JsonFileRepository(full_filepath, {})
            provider_data = json_repo.all_data
            
            if not provider_data:
                self.logger.warning(f"Le fichier {full_filepath} est vide.")
                raise ValueError(f"Données manquantes pour {provider_guid}")
            
            provider_model = self._dict_to_provider_model(provider_data)
            self.logger.info(f"Fournisseur chargé: {full_filepath}")
            return provider_model
        except Exception as e:
            self.logger.warning(f"Impossible de lire le fournisseur {full_filepath}: {e}")
            raise

    def list_all_providers(self) -> List[ProviderModel]:
        """Liste tous les fournisseurs disponibles.

        Parcourt le dossier des fournisseurs et retourne une liste de tous les 
        ProviderModel chargés avec succès.

        Returns:
            List[ProviderModel]: Une liste des fournisseurs trouvés.
                Retourne une liste vide si aucun fichier JSON n'existe.

        Exemples d'utilisation:
            >>> providers = repo.list_providers()
            >>> for provider in providers:
            ...     print(provider.provider_name)
        """
        providers: List[ProviderModel] = []
        
        for file_path in self._list_provider_files():
            try:
                json_repo = JsonFileRepository(file_path, {})
                provider_data = json_repo.all_data
                
                if provider_data:
                    provider_model = self._dict_to_provider_model(provider_data)
                    providers.append(provider_model)
                    self.logger.debug(f"Fournisseur ajouté à la liste: {file_path.name}")
            except Exception as e:
                self.logger.warning(f"Impossible de charger le provider {file_path.name}: {e}")
                continue
        
        self.logger.info(f"Total de {len(providers)} provider(s) chargé(s).")
        return providers

    def create_provider(self, provider: ProviderModel) -> None:
        """Enregistre un nouveau fournisseur.

        Convertit l'instance ProviderModel en dictionnaire et le sauvegarde dans un 
        fichier JSON via JsonFileRepository.

        Args:
            provider (ProviderModel): L'instance du fournisseur à sauvegarder.

        Raises:
            ValueError: Si le nom du fichier du provider est invalide.
            OSError: En cas d'erreur lors de l'écriture sur le disque.

        Exemples d'utilisation:
            >>> provider = ProviderModel()
            >>> repo.create_provider(provider)
        """
        # Construit le chemin complet du fichier
        full_filepath = self._folder_path / str(provider.provider_guid + ".json")
        
        # Crée le dossier s'il n'existe pas
        self.create_folder_if_missing()
        
        try:
            # Convertit le modèle en dictionnaire
            provider_dict = self._provider_model_to_dict(provider)
            
            # Crée un JsonFileRepository avec le dictionnaire vide comme défaut
            json_repo = JsonFileRepository(full_filepath, {})
            
            # Met à jour toutes les données avec celles du provider
            json_repo.all_data = provider_dict
            json_repo.save_to_file()
            
            self.logger.info(f"Fournisseur sauvegardé: {full_filepath}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du fournisseur: {e}")
            raise

    def update_provider(self, provider: ProviderModel) -> None:
        """Met à jour un fournisseur existant.

        Convertit l'instance ProviderModel en dictionnaire et le sauvegarde dans un 
        fichier JSON via JsonFileRepository.

        Args:
            provider (ProviderModel): L'instance du fournisseur à sauvegarder.

        Raises:
            ValueError: Si le nom du fichier du provider est invalide.
            OSError: En cas d'erreur lors de l'écriture sur le disque.

        Exemples d'utilisation:
            >>> provider = ProviderModel()
            >>> repo.update_provider(provider)
        """
        # Construit le chemin complet du fichier
        full_filepath = self._folder_path / str(provider.provider_guid + ".json")
        
        # Crée le dossier s'il n'existe pas
        self.create_folder_if_missing()
        
        try:
            # Convertit le modèle en dictionnaire
            provider_dict = self._provider_model_to_dict(provider)
            
            # Crée un JsonFileRepository avec le dictionnaire vide comme défaut
            json_repo = JsonFileRepository(full_filepath, {})
            
            # Met à jour toutes les données avec celles du provider
            json_repo.all_data = provider_dict
            json_repo.save_to_file()
            
            self.logger.info(f"Fournisseur sauvegardé: {full_filepath}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du fournisseur: {e}")
            raise

    def create_folder_if_missing(self):
        if not self._folder_path.exists():
            os.makedirs(self._folder_path, exist_ok=True)
            self.logger.info(f"Dossier créé: {self._folder_path}")

    def delete_provider(self, provider_guid: str) -> None:
        """Supprime un fournisseur.

        Supprime définitivement le fichier JSON correspondant au fournisseur du système de fichiers.

        Args:
            provider_guid (str): L'identifiant unique du fournisseur à supprimer.

        Raises:
            FileNotFoundError: Si le fichier cible n'existe pas.
            OSError: En cas de droits insuffisants ou si le fichier est verrouillé.

        Exemples d'utilisation:
            >>> repo.delete_provider("mon_provider")
        """
        self.logger.info("Ouverture du dossier des fournisseurs...")
        
        # Crée le dossier s'il n'existe pas
        self.create_folder_if_missing()

        # Cherche le fichier correspondant
        full_pathfile_to_delete = self.compute_fullpath_from_guid(provider_guid)
        
        if not full_pathfile_to_delete.exists():
            raise FileNotFoundError(f"Fournisseur non trouvé pour suppression: {provider_guid}")        
        
        try:
            os.remove(full_pathfile_to_delete)
            self.logger.info(f"Fournisseur supprimé: {full_pathfile_to_delete}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du fournisseur: {e}")
            raise

    def compute_fullpath_from_guid(self, provider_guid: str) -> Path:
        """Calcule le chemin complet du fichier JSON d'un fournisseur à partir de son identifiant.
        Args:
            provider_guid (str): L'identifiant unique du fournisseur.
            
        Returns:
            Path: Le chemin complet du fichier JSON du fournisseur.
        """
        return self._folder_path / (provider_guid + ".json")

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur.

        Déclenche l'affichage du dossier des fournisseurs dans l'explorateur système
        pour permettre à l'utilisateur de consulter ou d'éditer manuellement les fichiers JSON locaux.

        Raises:
            NotADirectoryError: Si le chemin spécifié n'est pas un dossier valide.

        Exemples d'utilisation:
            >>> repo.open_providers_folder()
        """
        self.logger.info("Ouverture du dossier des fournisseurs...")
        
        # Crée le dossier s'il n'existe pas
        self.create_folder_if_missing()
        
        if not self._folder_path.is_dir():
            raise NotADirectoryError(f"Le chemin spécifié n'est pas un dossier: {self._folder_path}")
        
        # Utilise le système d'exploitation pour ouvrir le dossier
        try:
            enum_os: OperatingSystem = detect_os()
            
            if enum_os == OperatingSystem.WINDOWS:
                os.startfile(self._folder_path)
            elif enum_os == OperatingSystem.MACOS:  # macOS et Linux
                subprocess.Popen(["open", self._folder_path])
            elif enum_os == OperatingSystem.LINUX:  # Linux
                subprocess.Popen(["xdg-open", self._folder_path])
            else:
                self.logger.warning(f"Système d'exploitation non pris en charge pour l'ouverture du dossier: {enum_os}")
                raise OSError(f"Système d'exploitation non pris en charge: {enum_os}")
            self.logger.info(f"Dossier ouvert: {self._folder_path}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ouverture du dossier: {e}")
            raise
