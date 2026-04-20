"""Module contenant le modèle de données pour un fournisseur.

Ce module définit la classe `ProviderModel` qui gère les données d'un fournisseur
(comme son nom et son URL) en utilisant un dépôt basé sur un fichier JSON.
"""

## ----------------------------------------------
## Imports
## ----------------------------------------------

from typing import Any

from repositories.json_repository import JsonFileRepository

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProviderModel:
    """Modèle représentant un fournisseur.

    Cette classe sert d'interface logicielle pour accéder et modifier les
    informations d'un fournisseur (nom, URL) stockées, par l'intermédiaire d'un
    référentiel basé sur un fichier JSON.

    Attributes:
        _repository (JsonFileRepository): L'instance du dépôt de données JSON utilisée pour
            lire et écrire les données du fournisseur.
    """
    _file_path: str
    _repository: JsonFileRepository

    def __init__(self, file_path: str) -> None:
        """Initialise une nouvelle instance de ProviderModel.

        Args:
            file_path (str): Le chemin vers le fichier JSON utilisé pour stocker 
                ou lire les données du fournisseur.

        Example:
            >>> modele = ProviderModel("data/fournisseur.json")
            >>> modele.provider_alias = "Mon Fournisseur"
            >>> print(modele.provider_alias)
            Mon Fournisseur
        """
        self._file_path: str = file_path
        self._repository = JsonFileRepository(self._file_path, {})

    @classmethod
    def get_default_data(cls, provider_alias: str, provider_filename: str) -> dict[str, Any]:
        """Retourne les données par défaut pour un nouveau fournisseur."""
        from datetime import datetime
        return {
            "provider_alias": provider_alias,
            "provider_filename": provider_filename,
            "url": "https://example.com",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0",
            "headless": True,
            "steps": []
        }

    ## ------------------------------------------
    ## Propriétés
    ## ------------------------------------------

    ## Propriété pour le chemin du fichier JSON
    @property
    def file_path(self) -> str:
        """str: Obtient ou définit le chemin du fichier JSON associé à ce fournisseur."""
        return self._file_path

    @file_path.setter
    def file_path(self, value: str) -> None:
        self._file_path = value
        self._repository = JsonFileRepository(self._file_path, {})

    ## Propriétés du Provider

    @property
    def provider_alias(self) -> str:
        return self._repository.get_value("provider_alias", "")

    @provider_alias.setter
    def provider_alias(self, value: str) -> None:
        self._repository.set_value("provider_alias", value)

    @property
    def provider_filename(self) -> str:
        return self._repository.get_value("provider_filename", "")

    @provider_filename.setter
    def provider_filename(self, value: str) -> None:
        self._repository.set_value("provider_filename", value)

    @property
    def url(self) -> str:
        return self._repository.get_value("url", "")

    @url.setter
    def url(self, value: str) -> None:
        self._repository.set_value("url", value)

    @property
    def created_date(self) -> str:
        return self._repository.get_value("created_date", "")

    @created_date.setter
    def created_date(self, value: str) -> None:
        self._repository.set_value("created_date", value)

    @property
    def version(self) -> str:
        return self._repository.get_value("version", "1.0.0")

    @version.setter
    def version(self, value: str) -> None:
        self._repository.set_value("version", value)

    @property
    def headless(self) -> bool:
        return self._repository.get_value("headless", True)

    @headless.setter
    def headless(self, value: bool) -> None:
        self._repository.set_value("headless", value)

    @property
    def steps(self) -> list[dict[str, Any]]:
        return self._repository.get_value("steps", [])

    @steps.setter
    def steps(self, value: list[dict[str, Any]]) -> None:
        self._repository.set_value("steps", value)
