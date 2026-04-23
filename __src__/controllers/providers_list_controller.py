"""Module contrôleur pour la vue de la liste des fournisseurs.

Ce module contient la classe `ProvidersListController` qui agit comme 
intermédiaire entre la vue (l'interface utilisateur), le modèle de données
et les services sous-jacents concernant la liste des différents fournisseurs
de scraping (lecture, suppression, ouverture de dossier et lancement global).

Exemples d'utilisation:
    >>> from services.provider_service import ProviderService
    >>> controller = ProvidersListController(provider_service, config_model)
    >>> controller.load_providers_into_view_model(mon_view_model)
"""

## ----------------------------------------------
## Imports
## ----------------------------------------------

import logging
from typing import TYPE_CHECKING

from models.config_aspirabot_model import ConfigAspirabotModel
from converters.providers_list_converter import ProvidersListConverter
from view_models.providers_list_view_model import ProvidersListViewModel

if TYPE_CHECKING:
    from services.provider_service import ProviderService

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersListController:
    """Contrôleur gérant l'affichage et la suppression des fournisseurs.

    Cette classe coordonne la communication entre le `ProviderService`
    et le `ProvidersListViewModel`. Elle gère également le lancement 
    des processus de scraping via la service métier.

    Attributes:
        provider_service (ProviderService): Service métier pour les opérations sur fournisseurs.
        config (ConfigAspirabotModel): Configuration globale de l'application.
        logger (logging.Logger): Logger spécifique au contrôleur.
        converter (ProvidersListConverter): Convertisseur de modèles vers les ViewModels.
    """

    def __init__(self, provider_service: "ProviderService", config: "ConfigAspirabotModel") -> None:
        """Initialise le contrôleur de la liste des fournisseurs.

        Args:
            provider_service (ProviderService): Le service métier pour les fournisseurs.
            config (ConfigAspirabotModel): Le modèle de configuration contenant
                les chemins de base.
        """
        self.provider_service = provider_service
        self.config = config
        self.logger = logging.getLogger(__name__)

    def load_providers_into_view_model(self, view_model: ProvidersListViewModel) -> None:
        """Parcourt les fournisseurs et les charge dans le ViewModel.

        Récupère la liste complète des fournisseurs via le service et construit
        les tuples (provider, stem) nécessaires au convertisseur.

        Args:
            view_model (ProvidersListViewModel): L'objet ViewModel devant être
                alimenté par la liste des fournisseurs trouvés.

        Returns:
            None
        """
        providers = self.provider_service.list_providers()
        view_model.providers = [ProvidersListConverter.to_item_view_model(p) for p in providers]
        view_model.update_count()

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur du système d'exploitation.

        Returns:
            None
        """
        self.logger.info("Ouverture du dossier des fournisseurs.")
        self.provider_service.open_providers_folder()

    def delete_provider(self, provider_guid: str) -> None:
        """Supprime le fichier d'un fournisseur ciblé par son ID.

        Args:
            provider_guid (str): L'identifiant unique du fournisseur à supprimer.

        Returns:
            None
        """
        self.logger.info(f"Fournisseur supprimé : {provider_guid}")
        self.provider_service.delete_provider(provider_guid)

    def launch_scraping(self, provider_filename: str) -> None:
        """Lance le processus de scraping pour un fournisseur donné.

        Délègue entièrement au service métier qui gère l'exécution asynchrone.

        Args:
            provider_filename (str): Le nom ou le stem du fournisseur à exécuter.

        Returns:
            None
        """
        self.logger.info(f"Lancement du scraping pour : {provider_filename}")
        try:
            self.provider_service.launch_scraping(provider_filename)
        except Exception as e:
            self.logger.error(f"Erreur lors du lancement du scraping {provider_filename}: {e}")
