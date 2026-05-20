"""Module contenant le présentateur pour la gestion des fournisseurs."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging

from services.historic_service import HistoricService
from views.historic_view import HistoricView


class HistoricPresenter:
    """Présentateur (Presenter) pour coordonner la vue et le service des fournisseurs.

    Ce présentateur écoute les interactions de la vue, exécute la logique
    métier via le service et met à jour la vue avec les nouvelles données.
    """

    def __init__(self, view: HistoricView, service: HistoricService) -> None:
        """Initialise le présentateur avec sa vue et son service affiliés.

        Args:
            view (ProviderView): L'interface utilisateur.
            service (ProviderService): Le service gérant la logique métier.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._service = service
