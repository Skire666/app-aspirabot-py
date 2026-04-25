"""Module contenant le modèle de données pour un fournisseur de scraping.

Ce module définit la classe `ProviderModel` qui représente les données d'un
fournisseur de manière pure, sans aucune dépendance vers l'infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
import uuid

@dataclass
class ProviderModel:
    """Modèle (entité) représentant un fournisseur.

    Cette classe pure ne contient que la structure de données d'un fournisseur
    et aucune logique de persistance ou d'infrastructure.
    """
    
    provider_guid: str
    provider_name: str
    url: str
    created_date: str
    modified_date: str
    version: str
    browser_displayed: bool
    automation_obfuscated: bool
    steps: List[Dict[str, Any]] = field(default_factory=list[Dict[str, Any]])

    @classmethod
    def get_default_data(cls) -> "ProviderModel":
        """Génère un nouveau fournisseur avec ses valeurs par défaut."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            provider_guid=str(uuid.uuid4()).lower(),
            provider_name="Nouv. Fournisseur",
            url="https://example.com",
            version="1.0.0",
            browser_displayed=True,
            automation_obfuscated=True,
            created_date=now,
            modified_date=now
        )
        
    def update_created_date_and_modified_date(self) -> None:
        """Met à jour les dates de création et de modification à l'instant présent."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created_date = now
        self.modified_date = now
    
    def update_modified_date(self) -> None:
        """Met à jour la date de modification à l'instant présent."""
        self.modified_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def is_valid_guid(value: str) -> bool:
        """Checks whether a value is a canonical UUID string.

        Args:
            value: Candidate GUID value.

        Returns:
            True when the value is a valid lowercase UUID string, otherwise False.
        """
        if not value:
            return False

        normalized_value = value.strip().lower()
        if not normalized_value:
            return False

        try:
            parsed_uuid = uuid.UUID(normalized_value)
        except (AttributeError, ValueError, TypeError):
            return False

        return str(parsed_uuid) == normalized_value

