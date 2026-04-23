"""Protocole pour le dépôt des fournisseurs.

Définit le contrat que doit respecter toute implémentation de dépôt pour les
fournisseurs, conformément à l'architecture propre."""

from typing import List, Protocol
from models.provider_model import ProviderModel

class ProviderRepositoryInterface(Protocol):
    """Interface pour le dépôt des fournisseurs."""

    def get_provider(self, provider_guid: str) -> ProviderModel:
        """Récupère un fournisseur par son identifiant."""
        ...

    def list_providers(self) -> List[ProviderModel]:
        """Liste tous les fournisseurs disponibles."""
        ...

    def save_provider(self, provider: ProviderModel) -> None:
        """Enregistre ou met à jour un fournisseur."""
        ...

    def delete_provider(self, provider_guid: str) -> None:
        """Supprime un fournisseur."""
        ...

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur."""
        ...

