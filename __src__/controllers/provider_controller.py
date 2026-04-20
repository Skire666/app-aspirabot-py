"""Contrôleur responsable de la gestion des fournisseurs.

Ce module contient la classe `ProviderController` qui fait le lien entre les vues,
les modèles (`AspirabotAppModel`, `ProviderModel`) et les dépôts de données
(`ProvidersRepository`, `FileManagerRepository`).
"""

## ----------------------------------------------
## Imports
## ----------------------------------------------

from typing import List

from models.aspirabot_app_model import AspirabotAppModel
from models.provider_model import ProviderModel
from repositories.providers_repository import ProvidersRepository
from repositories.file_manager_repository import FileManagerRepository

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProviderController:
    """Contrôleur gérant les opérations liées aux fournisseurs.

    Cette classe permet de créer des fournisseurs par défaut et d'ouvrir
    le répertoire de stockage contenant leurs fichiers de configuration sur le système.

    Attributes:
        config (AspirabotAppModel): Configuration principale de l'application
            contenant notamment le chemin du dossier des fournisseurs.
        repository (ProvidersRepository): Dépôt utilisé pour interagir avec
            les fichiers des fournisseurs dans le système de fichiers.
    """

    def __init__(self, config: AspirabotAppModel) -> None:
        """Initialise le contrôleur avec la configuration fournie.

        Args:
            config (AspirabotAppModel): L'instance du modèle de configuration
                de l'application contenant les paramètres d'environnement.
        """
        self.config = config
        self.repository = ProvidersRepository(self.config.folder_providers)

    def list_providers_available(self) -> List[str]:
        """Retourne une liste des noms de fichiers de fournisseurs disponibles.

        Cette méthode interroge le dépôt des fournisseurs pour obtenir les chemins
        des fichiers, puis extrait et retourne uniquement les noms de fichiers
        sans l'extension.

        Returns:
            list[str]: Une liste de noms de fichiers de fournisseurs (sans extension).
        """
        
        list_founds = self.repository.list_provider_files()

        return [file_path.stem for file_path in list_founds]
    
    def read_provider_content_selected(self, name_provider: str) -> ProviderModel:
        """Lit le contenu du fournisseur sélectionné et retourne une instance de ProviderModel.

        Args:
            name_provider (str): Le nom du fournisseur à lire (sans extension).

        Returns:
            ProviderModel: L'instance du fournisseur correspondant au nom fourni.

        Raises:
            FileNotFoundError: Si aucun fichier de fournisseur correspondant n'est trouvé.
        """
        return self.repository.read_provider_content_selected(name_provider)

    def create_default_provider(self) -> str:
        """Crée un fournisseur par défaut et le sauvegarde sur le disque.

        Génère un nouveau fichier de configuration de fournisseur en utilisant 
        un nom disponible automatique (ex: 'nouveau_provider' ou 'nouveau_provider_1')
        et y enregistre les données par défaut.

        Returns:
            str: Le nom d'identification du fichier créé sans l'extension (le 'stem').
            
        Example:
            >>> config = AspirabotAppModel()
            >>> controller = ProviderController(config)
            >>> controller.create_default_provider()
            'nouveau_provider'
        """
        available_path = self.repository.get_next_available_path("nouveau_provider")
        name_without_extension: str = available_path.stem
        default_data = ProviderModel.get_default_data(name_without_extension)
        self.repository.save_provider(available_path, default_data)
        return name_without_extension

    def check_folder_exists(self) -> bool:
        """Vérifie l'existence du dossier des fournisseurs via le dépôt.

        Returns:
            bool: True si le dossier existe, False sinon.
        """
        return self.repository.provider_folder_exists()

    def open_provider_folder(self) -> None:
        """Ouvre le dossier contenant les fichiers des fournisseurs dans l'explorateur.

        Fait appel au gestionnaire de fichiers natif du système d'exploitation 
        pour afficher le répertoire configuré (`self.config.folder_providers`).

        Example:
            >>> config = AspirabotAppModel()
            >>> controller = ProviderController(config)
            >>> controller.open_provider_folder()
            # Ouvre le dossier dans l'explorateur de fichiers de l'OS.
        """
        FileManagerRepository.open_folder(self.config.folder_providers)
