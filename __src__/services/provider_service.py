"""Service pour la gestion des fournisseurs de scraping."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging
from pathlib import Path

from interfaces.provider_repository_interface import ProviderRepositoryInterface
from models.provider_model import ProviderModel
from models.provider_validation_issue_model import ProviderValidationIssue
from models.provider_validation_report_model import ProviderValidationReport

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ProviderService:
    """Service contenant la logique métier pour les fournisseurs."""

    def __init__(self, repository: ProviderRepositoryInterface) -> None:
        """Initialise le service avec son dépôt.

        Args:
            repository: Le dépôt pour la persistance des fournisseurs.
        """
        self._repository = repository
        self._logger = logging.getLogger(__name__)

    def list_all_providers(self) -> list[ProviderModel]:
        """Liste tous les fournisseurs.

        Returns:
            Liste des modèles de fournisseurs.
        """
        return self._repository.list_all_providers()

    def read_provider(self, id_file: str) -> ProviderModel:
        """Récupère un fournisseur par son GUID.

        Args:
            id_file: L'identifiant unique du fournisseur.

        Returns:
            Le modèle du fournisseur.
        """
        model: ProviderModel = self._repository.read_provider(id_file)
        for step in model.steps:
            step.parent_context = model
        return model

    def exists_provider(self, id_file: str) -> bool:
        """Vérifie l'existence d'un fournisseur.

        Args:
            id_file: L'identifiant unique à vérifier.

        Returns:
            True si le fournisseur existe, False sinon.
        """
        return self._repository.exists_provider(id_file)

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

    def delete_provider(self, id_file: str) -> None:
        """Supprime un fournisseur existant.

        Args:
            id_file: Le GUID du fournisseur à supprimer.
        """
        self._repository.delete_provider(id_file)

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur du système."""
        self._repository.open_providers_folder()

    def validate_providers(self) -> ProviderValidationReport:
        """Validates every provider file and moves broken files away.

        Returns:
            The summary of the validation run.
        """
        provider_files = self._repository.list_provider_files()

        valid_files = 0
        issues: list[ProviderValidationIssue] = []

        self._logger.info("Démarrage de la validation des fournisseurs pour %s fichier(s).", len(provider_files))

        for file_path in provider_files:
            reasons = self._collect_validation_reasons(file_path)

            if reasons:
                broken_path = ""
                try:
                    moved_path = self._repository.move_invalid_provider_file(file_path, "; ".join(reasons))
                    broken_path = str(moved_path)
                except Exception as exc:
                    move_reason = f"Unable to move invalid file: {exc}"
                    reasons.append(move_reason)
                    self._logger.exception("Failed to move invalid file %s.", file_path)

                issues.append(
                    ProviderValidationIssue(
                        file_name=file_path.name,
                        original_path=str(file_path),
                        broken_path=broken_path,
                        reasons=reasons,
                    )
                )
                self._logger.warning("Invalid provider file %s: %s", file_path.name, "; ".join(reasons))
                continue

            valid_files += 1

        report = ProviderValidationReport(
            total_files=len(provider_files),
            valid_files=valid_files,
            invalid_files=len(issues),
            issues=issues,
        )
        self._logger.info(
            "Providers validation completed: %s total, %s valid, %s invalid.",
            report.total_files,
            report.valid_files,
            report.invalid_files,
        )
        return report

    def _collect_validation_reasons(self, file_path: Path) -> list[str]:
        """Collects validation issues for a provider file.

        Args:
            file_path: File to validate.

        Returns:
            A list of validation reasons. An empty list means the file is valid.
        """
        reasons: list[str] = []

        try:
            if file_path.stat().st_size == 0:
                reasons.append("Fichier vide")
                return reasons
        except OSError as exc:
            reasons.append(f"Fichier illisible: {exc}")
            return reasons

        try:
            provider_data = self._repository.read_provider_content(file_path)
        except Exception as exc:
            reasons.append(f"Contenu corrompu ou illisible: {exc}")
            return reasons

        id_file = provider_data.get("id_file")
        if not isinstance(id_file, str) or not id_file.strip():
            reasons.append("Champ ID manquant")
            return reasons

        normalized_id = id_file.strip().lower()
        if not ProviderModel.is_valid_id(normalized_id):
            reasons.append("Format ID invalide")

        if file_path.stem.lower() != normalized_id:
            reasons.append("Nom de fichier non conforme au ID")

        return reasons
