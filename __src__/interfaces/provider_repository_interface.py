"""Protocole pour le dépôt des fournisseurs.

Définit le contrat que doit respecter toute implémentation de dépôt pour les
fournisseurs, conformément à l'architecture propre.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Protocol

from models.provider_model import ProviderModel


class ProviderRepositoryInterface(Protocol):
    """Interface pour le dépôt des fournisseurs."""

    def exists_provider(self, id_file: str) -> bool:
        """Vérifie l'existence d'un fournisseur par son identifiant."""
        ...

    def read_provider(self, id_file: str) -> ProviderModel:
        """Récupère un fournisseur par son identifiant."""
        ...

    def list_all_providers(self) -> list[ProviderModel]:
        """Liste tous les fournisseurs disponibles."""
        ...

    def list_provider_files(self) -> list[Path]:
        """Liste tous les fichiers présents dans le dossier des fournisseurs."""
        ...

    def read_provider_content(self, file_path: Path) -> dict[str, Any]:
        """Lit et retourne le contenu JSON brut d'un fichier fournisseur."""
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
