"""Module contrôleur pour la vue de la liste des fournisseurs.

Ce module contient la classe `ProvidersListController` qui agit comme 
intermédiaire entre la vue (l'interface utilisateur), le modèle de données
et les services sous-jacents concernant la liste des différents fournisseurs
de scraping (lecture, suppression, ouverture de dossier et lancement global).

Exemples d'utilisation:
    >>> controller = ProvidersListController(config_model)
    >>> controller.load_providers_into_view_model(mon_view_model)
"""

## ----------------------------------------------
## Imports
## ----------------------------------------------

import logging

from repositories.providers_repository import ProvidersRepository
from models.config_aspirabot_model import ConfigAspirabotModel
from models.provider_model import ProviderModel
from converters.providers_list_converter import ProvidersListConverter
from view_models.providers_list_view_model import ProvidersListViewModel

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersListController:
    """Contrôleur gérant l'affichage et la suppression des fournisseurs.

    Cette classe coordonne la communication entre le `ProvidersRepository`
    et le `ProvidersListViewModel`. Elle gère également le lancement 
    des processus de scraping asynchrones dans des threads distincts.

    Attributes:
        config (ConfigAspirabotModel): Configuration globale de l'application.
        logger (logging.Logger): Logger spécifique au contrôleur.
        repository (ProvidersRepository): Accès aux données des fournisseurs.
        converter (ProvidersListConverter): Convertisseur de modèles vers les ViewModels.
    """

    def __init__(self, config: ConfigAspirabotModel) -> None:
        """Initialise le contrôleur de la liste des fournisseurs.

        Args:
            config (ConfigAspirabotModel): Le modèle de configuration contenant
                les chemins de base (notamment `folder_providers`).
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.repository = ProvidersRepository(self.config.folder_providers)
        self.converter = ProvidersListConverter()

    def load_providers_into_view_model(self, view_model: ProvidersListViewModel) -> None:
        """Parcourt les fichiers fournisseurs et les charge dans le ViewModel.

        Args:
            view_model (ProvidersListViewModel): L'objet ViewModel devant être
                alimenté par la liste des fournisseurs trouvés.

        Returns:
            None
        """
        files = self.repository.list_provider_files()
        
        providers_tuples: list[tuple[ProviderModel, str]] = []
        for file in files:
            stem = file.stem
            try:
                provider = self.repository.read_provider_content_selected(stem)
                providers_tuples.append((provider, stem))
            except Exception:
                # Les fichiers illisibles sont silencieusement ignorés pour ne pas bloquer l'UI
                pass
                
        self.converter.to_view_model(providers_tuples, view_model)

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur du système d'exploitation.

        Returns:
            None
        """
        self.logger.info("Ouverture du dossier des fournisseurs.")
        self.repository.open_providers_folder()

    def delete_provider(self, provider_filename: str) -> None:
        """Supprime le fichier d'un fournisseur ciblé par son nom de fichier.

        Args:
            provider_filename (str): Le nom complet du fichier (ex: "amazon.json").

        Returns:
            None
        """
        self.logger.info(f"Fournisseur supprimé : {provider_filename}")
        self.repository.delete_provider(provider_filename)

    def launch_scraping(self, provider_filename: str) -> None:
        """Lance le processus de scraping pour un fournisseur donné dans un thread d'arrière-plan.

        Crée un processus asynchrone Playwright qui ne bloque pas l'interface Tkinter principale.

        Args:
            provider_filename (str): Le nom ou le stem du fournisseur à exécuter.

        Returns:
            None
        """
        self.logger.info(f"Lancement du scraping pour : {provider_filename}")
        try:
            provider = self.repository.read_provider_content_selected(provider_filename)
        except Exception as e:
            self.logger.error(f"Erreur de lecture du fournisseur {provider_filename}: {e}")
            return
            
        import threading
        import asyncio
        from utils.web_browser_util import run_scraping_task
        
        def run_async() -> None:
            asyncio.run(run_scraping_task(provider))
            
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

