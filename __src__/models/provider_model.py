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
    
    provider_guid: str = ""
    provider_title: str = "Nouv. Fournisseur"
    url: str = "https://example.com"
    created_date: str = ""
    modified_date: str = ""
    version: str = "1.0.0"
    browser_displayed: bool = True
    automation_obfuscated: bool = True
    steps: List[Dict[str, Any]] = field(default_factory=list[Dict[str, Any]])

    @classmethod
    def get_default_data(cls) -> "ProviderModel":
        """Génère un nouveau fournisseur avec ses valeurs par défaut."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            provider_guid=str(uuid.uuid4()).lower(),
            provider_title="Nouv. Fournisseur",
            created_date=now,
            modified_date=now
        )
        
    def update_modified_date(self) -> None:
        """Met à jour la date de modification à l'instant présent."""
        self.modified_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

