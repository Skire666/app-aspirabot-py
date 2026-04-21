"""ViewModel pour l'écran de création/édition d'un fournisseur.

Agissant comme abstraction (Data-Binding) pour le panneau `UpdatePanelView`,
il permet notamment de vérifier la logique de validation de la configuration
avant tout passage et de modifier ces informations sans impacter le stockage.

Exemples d'utilisation:
    >>> vm = UpdateViewModel()
    >>> list_erreurs = vm.validate()
"""

import tkinter as tk
from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class UpdateViewModel:
    """Conteneur d'états réactifs pour l'éditeur de Fournisseur Tkinter.

    Structure regroupant toutes les `tk.Variable` utiles avec
    une liste mutable d'étapes que Playwright exécutera au moment opportun.
    
    Attributes:
        provider_filename (tk.StringVar): Nom imposé ou lu du fichier `.json`.
        provider_title (tk.StringVar): Nom métier du fournisseur.
        url (tk.StringVar): Point d'entrée scraping du fournisseur HTTP(S).
        created_date (tk.StringVar): Moment de la première initialisation.
        modified_date (tk.StringVar): Dernière variation de sauvegarde.
        version (tk.StringVar): Version interne du JSON (ex. "1.0").
        browser_displayed (tk.BooleanVar): Active ou non l'affichage visible de Playwright (headful vs headless).
        automation_obfuscated (tk.BooleanVar): Désactive les arguments Playwright anti-bot basiques.
        steps (List[dict[str, Any]]): Instructions paramétrées (FIND_ELEMENT, CLICK, WAIT...).
    """
    provider_filename: tk.StringVar = field(default_factory=tk.StringVar)
    provider_title: tk.StringVar = field(default_factory=tk.StringVar)
    url: tk.StringVar = field(default_factory=tk.StringVar)
    created_date: tk.StringVar = field(default_factory=tk.StringVar)
    modified_date: tk.StringVar = field(default_factory=tk.StringVar)
    version: tk.StringVar = field(default_factory=tk.StringVar)
    browser_displayed: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    automation_obfuscated: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    steps: List[dict[str, Any]] = field(default_factory=list) # type: ignore[reportUnknownVariableType]

    def validate(self) -> List[str]:
        """Contrôle d'intégrité métier pour l'UI Tkinter et ses bindings visuels.

        Appliqué pour garantir l'absence d'étapes caduques (un CLICK sans selecteur),
        ou de configuration principale manquante/trop courte (Titre < 3 car).

        Returns:
            List[str]: Une liste d'anomalies bloquantes formatées en chaînes de texte.
                Vide [] signifie "valide".

        Exemples d'utilisation:
            >>> validateur = vm.validate()
        """
        errors: List[str] = []
        if not self.provider_title.get() or not self.provider_title.get().strip() or len(self.provider_title.get().strip()) < 3:
            errors.append("Le champ 'Nom' est obligatoire (3 caractères minimum).")
        if not self.provider_filename.get() or not self.provider_filename.get().strip():
            errors.append("Le champ 'Nom de fichier' est obligatoire.")
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
