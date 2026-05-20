"""Service pour la gestion des fournisseurs de scraping."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging

from interfaces.provider_repository_interface import ProviderRepositoryInterface

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class HistoricService:
    """Service contenant la logique métier pour les fournisseurs."""

    def __init__(self, repository: ProviderRepositoryInterface) -> None:
        """Initialise le service avec son dépôt.

        Args:
            repository: Le dépôt pour la persistance des fournisseurs.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository
