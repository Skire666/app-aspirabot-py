"""Service pour la gestion des fournisseurs de scraping."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from interfaces.i_scenarios_repository import IScenariosRepository
from models.scenario_model import ProviderModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScenariosService:
    """Service contenant la logique métier pour les fournisseurs."""

    def __init__(self, repository: IScenariosRepository) -> None:
        """Initialise le service avec son dépôt.

        Args:
            repository: Le dépôt pour la persistance des fournisseurs.
        """
        self._logger = logging.getLogger(__name__)
        self._repository: IScenariosRepository = repository

    def list_all_scenarios(self) -> list[ProviderModel]:
        """Liste tous les fournisseurs.

        Returns:
            Liste des modèles de fournisseurs.
        """
        return self._repository.read_all_scenarios()

    def read_provider(self, id_file: str) -> ProviderModel:
        """Récupère un fournisseur par son GUID.

        Args:
            id_file: L'identifiant unique du fournisseur.

        Returns:
            Le modèle du fournisseur.
        """
        model = self._repository.read_scenario(id_file)
        for step in model.steps:
            step.parent_context = model.steps
        return model

    def exists_provider(self, id_file: str) -> bool:
        """Vérifie l'existence d'un fournisseur.

        Args:
            id_file: L'identifiant unique à vérifier.

        Returns:
            True si le fournisseur existe, False sinon.
        """
        return self._repository.exists_scenario(id_file)

    def create_provider(self, provider: ProviderModel) -> None:
        """Crée un nouveau fournisseur avec ses timestamps mis à jour.

        Args:
            provider: Le modèle du fournisseur à créer.
        """
        provider.mark_as_created()
        self._repository.create_scenario(provider)

    def update_provider(self, provider: ProviderModel) -> None:
        """Met à jour un fournisseur existant.

        Args:
            provider: Le modèle du fournisseur à mettre à jour.
        """
        provider.mark_as_modified()
        self._repository.update_scenario(provider)

    def duplicate_provider(self, id_file: str) -> str:
        """Duplique un fournisseur existant et persiste la copie.

        Args:
            id_file: L'identifiant du fournisseur source.

        Returns:
            L'identifiant du nouveau fournisseur créé.
        """
        original = self._repository.read_scenario(id_file)
        copy = ProviderModel.copy_business(original)
        self.create_provider(copy)
        return copy.id_file

    def delete_provider(self, id_file: str) -> None:
        """Supprime un fournisseur existant.

        Args:
            id_file: Le GUID du fournisseur à supprimer.
        """
        self._repository.delete_scenario(id_file)

    def open_scenarios_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur du système."""
        self._repository.open_scenarios_folder()

    def get_folder_path_scenarios(self) -> str:
        """Récupère le chemin du dossier des fournisseurs.

        Returns:
            Le chemin du dossier des fournisseurs.
        """
        return self._repository.get_path_scenarios_folder()
