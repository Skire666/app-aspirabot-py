"""Module contenant le modèle de données pour un fournisseur de scraping.

Ce module définit la classe `ProviderModel` qui gère les données d'un fournisseur
(comme son nom, son URL, ses options et ses étapes) en interagissant avec
un dépôt basé sur un fichier JSON (JsonFileRepository). Il assure l'accès,
la persistance et la gestion des données de configuration liées à chaque source.

Exemples d'utilisation:
    >>> from models.provider_model import ProviderModel
    >>> modele = ProviderModel("data/nouveau_fournisseur.json")
    >>> data = ProviderModel.get_default_data("Nom", "nom_fichier")
    >>> modele.provider_title = "Nouveau Fournisseur"
"""

## ----------------------------------------------
## Imports
## ----------------------------------------------

from typing import Any, Dict, List

from repositories.json_repository import JsonFileRepository

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProviderModel:
    """Modèle représentant un fournisseur.

    Cette classe sert d'interface logicielle pour accéder et modifier les
    informations d'un fournisseur (nom, URL, variables, options, étapes) 
    stockées, par l'intermédiaire d'un référentiel basé sur un fichier JSON.

    Attributes:
        _file_path (str): Le chemin absolu ou relatif vers le fichier de configuration JSON.
        _repository (JsonFileRepository): L'instance du dépôt de données JSON 
            utilisée pour lire et écrire les données sur le disque.
    """
    _file_path: str
    _repository: JsonFileRepository

    def __init__(self, file_path: str) -> None:
        """Initialise une nouvelle instance de ProviderModel liée à un chemin JSON.

        Args:
            file_path (str): Le chemin vers le fichier JSON utilisé pour stocker 
                ou lire les données du fournisseur.

        Raises:
            IOError: Si le JsonFileRepository échoue à lire les données.
            
        Exemples d'utilisation:
            >>> modele = ProviderModel("data/fournisseur.json")
            >>> modele.url = "https://nouveau.fournisseur"
        """
        self._file_path: str = file_path
        self._repository = JsonFileRepository(self._file_path, {})

    @classmethod
    def get_default_data(cls, provider_title: str, provider_filename: str) -> Dict[str, Any]:
        """Génère l'ensemble de données par défaut d'un nouveau fournisseur.
        
        Permet de fournir un dictionnaire structuré prêt à être sauvegardé
        en cas de création de fournisseur vierge ou si le fichier d'origine
        n'en contient pas un complet.

        Args:
            provider_title (str): Le titre affichable du fournisseur.
            provider_filename (str): Le nom du fichier sécurisé associé.

        Returns:
            Dict[str, Any]: Dictionnaire contenant les propriétés par défaut 
            nécessaires au bon fonctionnement de l'application (dates, booléens, infos).
            
        Exemples d'utilisation:
            >>> data = ProviderModel.get_default_data("Nouv", "nouv_fournisseur")
            >>> assert "version" in data
        """
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "provider_title": provider_title,
            "provider_filename": provider_filename,
            "url": "https://example.com",
            "created_date": now,
            "modified_date": now,
            "version": "1.0.0",
            "browser_displayed": True,
            "automation_obfuscated": True,
            "steps": []
        }
        
    def save_to_file(self) -> None:
        """Enregistre les données actuelles du fournisseur dans le fichier JSON associé.

        Cette méthode doit être appelée après avoir modifié les propriétés du modèle
        pour assurer que les changements soient persistés sur le disque.

        Raises:
            IOError: Si l'écriture dans le fichier JSON échoue.
            
        Exemples d'utilisation:
            >>> modele.url = "https://nouveau.fournisseur"
            >>> modele.save_to_file()
        """
        self._repository.save_to_file()

    ## ------------------------------------------
    ## Propriétés
    ## ------------------------------------------

    ## Propriété pour le chemin du fichier JSON
    @property
    def file_path(self) -> str:
        """str: Obtient ou définit le chemin du fichier JSON associé.
        
        Lorsqu'il est défini, recrée automatiquement l'objet JsonFileRepository.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, value: str) -> None:
        self._file_path = value
        self._repository = JsonFileRepository(self._file_path, {})

    ## Propriétés du Provider

    @property
    def provider_title(self) -> str:
        """str: Récupère ou modifie le titre d'affichage du fournisseur."""
        return self._repository.get_value("provider_title", "Nouv. Fournisseur")

    @provider_title.setter
    def provider_title(self, value: str) -> None:
        self._repository.set_value("provider_title", value)

    @property
    def provider_filename(self) -> str:
        """str: Récupère ou modifie le nom sécurisé du fichier fournisseur."""
        return self._repository.get_value("provider_filename", "nouv_fournisseur.json")

    @provider_filename.setter
    def provider_filename(self, value: str) -> None:
        self._repository.set_value("provider_filename", value)

    @property
    def url(self) -> str:
        """str: Récupère ou modifie l'URL racine ciblée par le fournisseur."""
        return self._repository.get_value("url", "https://example.com")

    @url.setter
    def url(self, value: str) -> None:
        self._repository.set_value("url", value)

    @property
    def created_date(self) -> str:
        """str: Récupère ou modifie la date de création au format 'AAAA-MM-JJ HH:MM:SS'."""
        return self._repository.get_value("created_date", "")

    @created_date.setter
    def created_date(self, value: str) -> None:
        self._repository.set_value("created_date", value)

    @property
    def version(self) -> str:
        """str: Récupère ou modifie la version de configuration métier (ex: '1.0.0')."""
        return self._repository.get_value("version", "1.0.0")

    @version.setter
    def version(self, value: str) -> None:
        self._repository.set_value("version", value)

    @property
    def browser_displayed(self) -> bool:
        """bool: Obtient ou définit l'affichage du navigateur Playwright (mode headless/headed)."""
        return self._repository.get_value("browser_displayed", True)

    @browser_displayed.setter
    def browser_displayed(self, value: bool) -> None:
        self._repository.set_value("browser_displayed", value)

    @property
    def automation_obfuscated(self) -> bool:
        """bool: Obtient ou définit l'utilisation des extensions contre le contrôle d'automatisation."""
        return self._repository.get_value("automation_obfuscated", True)

    @automation_obfuscated.setter
    def automation_obfuscated(self, value: bool) -> None:
        self._repository.set_value("automation_obfuscated", value)

    @property
    def modified_date(self) -> str:
        """str: Récupère ou modifie la date de la dernière mise à jour."""
        return self._repository.get_value("modified_date", "")

    @modified_date.setter
    def modified_date(self, value: str) -> None:
        self._repository.set_value("modified_date", value)

    @property
    def steps(self) -> List[Dict[str, Any]]:
        """List[Dict[str, Any]]: Récupère ou modifie la liste des étapes du scraping."""
        return self._repository.get_value("steps", [])

    @steps.setter
    def steps(self, value: List[Dict[str, Any]]) -> None:
        self._repository.set_value("steps", value)
