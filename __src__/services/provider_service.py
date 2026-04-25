"""Service pour la gestion des fournisseurs de scraping."""

from typing import List
from models.provider_model import ProviderModel
from interfaces.provider_repository_interface import ProviderRepositoryInterface

class ProviderService:
    """Service contenant la logique métier pour les fournisseurs."""

    def __init__(self, repository: ProviderRepositoryInterface) -> None:
        """Initialise le service avec son dépôt.

        Args:
            repository: Le dépôt pour la persistance des fournisseurs.
        """
        self._repository = repository

    def list_providers(self) -> List[ProviderModel]:
        """Liste tous les fournisseurs.
        
        Returns:
            Liste des modèles de fournisseurs.
        """
        return self._repository.list_all_providers()

    def get_provider(self, provider_guid: str) -> ProviderModel:
        """Récupère un fournisseur par son GUID.
        
        Args:
            provider_guid: L'identifiant unique du fournisseur.
            
        Returns:
            Le modèle du fournisseur.
        """
        return self._repository.read_provider(provider_guid)

    def exists_provider(self, provider_guid: str) -> bool:
        """Vérifie l'existence d'un fournisseur.
        
        Args:
            provider_guid: L'identifiant unique à vérifier.
            
        Returns:
            True si le fournisseur existe, False sinon.
        """
        return self._repository.exists_provider(provider_guid)

    def create_provider(self, provider: ProviderModel) -> None:
        """Crée un nouveau fournisseur avec ses timestamps mis à jour.
        
        Args:
            provider: Le modèle du fournisseur à créer.
        """
        provider.update_created_date_and_modified_date()
        self._repository.create_provider(provider)

    def update_provider(self, provider: ProviderModel) -> None:
        """Met à jour un fournisseur existant.
        
        Args:
            provider: Le modèle du fournisseur à mettre à jour.
        """
        provider.update_modified_date()
        self._repository.update_provider(provider)

    def delete_provider(self, provider_guid: str) -> None:
        """Supprime un fournisseur existant.
        
        Args:
            provider_guid: Le GUID du fournisseur à supprimer.
        """
        self._repository.delete_provider(provider_guid)

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur du système."""
        self._repository.open_providers_folder()
