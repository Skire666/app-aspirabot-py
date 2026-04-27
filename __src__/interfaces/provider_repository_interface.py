"""Protocole pour le dépôt des fournisseurs.

Définit le contrat que doit respecter toute implémentation de dépôt pour les
fournisseurs, conformément à l'architecture propre.
"""

from pathlib import Path
from typing import Any, Dict, List, Protocol

from models.provider_model import ProviderModel


class ProviderRepositoryInterface(Protocol):
    """Interface pour le dépôt des fournisseurs."""

    def exists_provider(self, id_file: str) -> bool:
        """Vérifie l'existence d'un fournisseur par son identifiant."""
        ...

    def read_provider(self, id_file: str) -> ProviderModel:
        """Récupère un fournisseur par son identifiant."""
        ...

    def list_all_providers(self) -> List[ProviderModel]:
        """Liste tous les fournisseurs disponibles."""
        ...

    def list_provider_files(self) -> List[Path]:
        """Liste tous les fichiers présents dans le dossier des fournisseurs."""
        ...

    def read_provider_file_data(self, file_path: Path) -> Dict[str, Any]:
        """Lit et retourne le contenu JSON brut d'un fichier fournisseur."""
        ...

    def ensure_broken_folder(self) -> Path:
        """Crée le dossier des fichiers invalides si nécessaire."""
        ...

    def move_invalid_provider_file(self, file_path: Path, reason: str) -> Path:
        """Déplace un fichier invalide vers le dossier des fichiers cassés."""
        ...

    def create_provider(self, provider: ProviderModel) -> None:
        """Crée un nouveau fournisseur."""
        ...

    def update_provider(self, provider: ProviderModel) -> None:
        """Met à jour un fournisseur."""
        ...

    def delete_provider(self, id_file: str) -> None:
        """Supprime un fournisseur."""
        ...

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur."""
        ...
