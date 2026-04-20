import tkinter as tk
from dataclasses import dataclass, field
from typing import List

@dataclass
class ProviderItemViewModel:
    provider_filename: str = ""
    provider_alias: str = ""
    url: str = ""
    created_date: str = ""

@dataclass
class ProvidersListViewModel:
    """Représente les données de la liste des fournisseurs."""
    providers: List[ProviderItemViewModel] = field(default_factory=list[ProviderItemViewModel])
    count_text: tk.StringVar = field(default_factory=tk.StringVar)
    
    def update_count(self) -> None:
        count = len(self.providers)
        str_display = self._format_provider_counter(count)
        self.count_text.set(str_display)

    def _format_provider_counter(self, count: int) -> str:
        """

        Args:
            count (int): _description_

        Returns:
            str: _description_
        """
        if count == 0:
            return "Aucun fournisseur disponible"
        return f"{count} fournisseur{'s' if count > 1 else ''}"
