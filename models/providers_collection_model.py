"""Module responsable de la gestion des collections de fournisseurs.

Ce module définit la classe `ProvidersCollectionModel` qui interagit avec
le dépôt de fournisseurs pour récupérer et formater les données des fournisseurs.
"""

## ----------------------------------------------
## Imports
## ----------------------------------------------

from repositories.providers_repository import ProvidersRepository
from models.aspirabot_app_model import AspirabotAppModel


class ProvidersCollectionModel:
    """Modèle représentant une collection de fournisseurs (providers).

    Cette classe sert d'interface entre la logique de l'application et la couche
    d'accès aux données (ProviderRepository) pour gérer plusieurs fournisseurs.

    Attributes:
        _repository (ProviderRepository): L'instance du dépôt utilisée pour
            accéder aux données des fournisseurs.
    """

    def __init__(self, config: AspirabotAppModel) -> None:
        """Initialise une nouvelle instance de ProvidersCollectionModel.

        Args:
            config (AspirabotAppModel): La configuration principale de l'application
                nécessaire pour initialiser le dépôt des fournisseurs.

        Example:
            >>> config = AspirabotAppModel(...)
            >>> collection = ProvidersCollectionModel(config)
        """
        self._repository = ProvidersRepository(config.folder_providers)
