"""Modèle de vue (ViewModel) pour l'interface WYSIWYG.

Ce module contient la définition du `WysiwygViewModel`, qui représente
les données formatées spécifiquement pour l'affichage et l'édition dans la vue.
"""

import tkinter as tk
from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class WysiwygViewModel:
    """Représente les données affichées dans l'interface WYSIWYG.
    
    Toutes les données sont formatées pour la vue (ex: les tags en une seule 
    chaîne de caractères).
    """
    provider_name: tk.StringVar = field(default_factory=tk.StringVar)
    url: tk.StringVar = field(default_factory=tk.StringVar)
    created_date: tk.StringVar = field(default_factory=tk.StringVar)
    version: tk.StringVar = field(default_factory=tk.StringVar)
    tags_str: tk.StringVar = field(default_factory=tk.StringVar)
    headless: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    steps: List[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Vérifie la validité des données du ViewModel.
        
        Returns:
            list[str]: Une liste de messages d'erreur. Si la liste est vide, les données sont valides.
        """
        errors: list[str] = []
        if not self.provider_name.get() or not self.provider_name.get().strip():
            errors.append("Le champ 'Nom' est obligatoire.")
        if not self.url.get() or not self.url.get().strip():
            errors.append("Le champ 'URL' est obligatoire.")
            
        for idx, step in enumerate(self.steps):
            t = step.get("type")
            if t in ["FIND_ELEMENT", "CLICK", "EXTRACT_TEXT"]:
                if not step.get("selector"):
                    errors.append(f"Étape {idx + 1} ({t}) : le sélecteur est requis.")
            elif t == "WAIT":
                if not step.get("timeout") and not step.get("selector"):
                    errors.append(f"Étape {idx + 1} ({t}) : timeout ou sélecteur est requis.")
        return errors
