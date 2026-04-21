"""ViewModel pour la liste des fournisseurs.

Fournit les structures de données (dataclasses) requises
par l'interface d'affichage pour présenter la collection des fournisseurs,
gérant les textes réactifs (comme le compteur).

Exemples d'utilisation:
    >>> vm = ProvidersListViewModel()
    >>> list_item = ProviderItemViewModel("f1.json", "Fournisseur Un", "http://", "2026", "2026", "1.0.0")
"""

import tkinter as tk
from dataclasses import dataclass, field
from typing import List

@dataclass
class ProviderItemViewModel:
    """Représente les données d'un fournisseur unique pour présentation (liste).

    Ceci masque ou transforme partiellement la complexité du `ProviderModel`.
    
    Attributes:
        provider_filename (str): Nom du fichier physique porteur du fournisseur.
        provider_title (str): Titre humain ou d'affichage.
        url (str): Lien principal du fournisseur pour le ciblage.
        created_date (str): Date d'intégration logicielle.
        modified_date (str): Dernière altération de modèle/donnée.
        version (str): Schéma de version pour rétrocompatibilité.
    """
    provider_filename: str = ""
    provider_title: str = ""
    url: str = ""
    created_date: str = ""
    modified_date: str = ""
    version: str = ""

@dataclass
class ProvidersListViewModel:
    """Gère l'information globale rattachée à la vue de la liste des fournisseurs.

    Attributes:
        providers (List[ProviderItemViewModel]): Ensemble des fournisseurs préparés.
        count_text (tk.StringVar): Variable dynamique du compteur Tkinter.
    """
    providers: List[ProviderItemViewModel] = field(default_factory=list)
    count_text: tk.StringVar = field(default_factory=tk.StringVar)
    
    def update_count(self) -> None:
        """Met à jour le contenu de `count_text` en fonction de la taille de `providers`.
        
        Exemples d'utilisation:
            >>> vm.providers.append(ProviderItemViewModel())
            >>> vm.update_count()
        """
        count = len(self.providers)
        str_display = self._format_provider_counter(count)
        self.count_text.set(str_display)

    def _format_provider_counter(self, count: int) -> str:
        """Génère le libellé humanisé pour le compteur de fournisseurs.

        Args:
            count (int): Le nombre total d'entités trouvées.

        Returns:
            str: Le texte formatté ("Aucun fournisseur", "1 fournisseur", "2 fournisseurs").
            
        Exemples d'utilisation:
            >>> titre = vm._format_provider_counter(4)
        """
        if count == 0:
            return "Aucun fournisseur disponible"
        return f"{count} fournisseur{'s' if count > 1 else ''}"
