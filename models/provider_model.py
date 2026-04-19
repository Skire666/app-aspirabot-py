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
            >>> modele.provider_name = "Mon Fournisseur"
            >>> print(modele.provider_name)
            Mon Fournisseur
        """
        self._file_path: str = file_path
        self._repository = JsonFileRepository(self._file_path, {})

    @classmethod
    def get_default_data(cls, provider_name: str) -> dict[str, Any]:
        """Retourne les données par défaut pour un nouveau fournisseur."""
        from datetime import datetime
        return {
            "provider_name": provider_name,
            "url": "https://example.com",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0",
            "tags": [],
            "headless": True
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
    def provider_name(self) -> str:
        return self._repository.get_value("provider_name", "")

    @provider_name.setter
    def provider_name(self, value: str) -> None:
        self._repository.set_value("provider_name", value)

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
    def tags(self) -> list[str]:
        return self._repository.get_value("tags", [])

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._repository.set_value("tags", value)

    @property
    def headless(self) -> bool:
        return self._repository.get_value("headless", True)

    @headless.setter
    def headless(self, value: bool) -> None:
        self._repository.set_value("headless", value)
